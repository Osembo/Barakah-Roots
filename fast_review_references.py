import pandas as pd
import requests
import time
import re
from urllib.parse import quote

# Load Excel
df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")
df = df.dropna(subset=["Compound Name"])

def parse_species(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(";")]

# Build species -> references mapping
species_refs = {}
for _, row in df.iterrows():
    species_list = parse_species(row["Species"])
    if not species_list:
        continue
    pmids = []
    if pd.notna(row["PMIDs"]):
        pmids = [p.strip() for p in str(row["PMIDs"]).split(";") if p.strip().isdigit()]
    links = []
    if pd.notna(row["Links"]):
        links = [l.strip() for l in str(row["Links"]).split(";") if l.strip()]
    for sp in species_list:
        if sp not in species_refs:
            species_refs[sp] = {"pmids": set(), "links": set()}
        species_refs[sp]["pmids"].update(pmids)
        species_refs[sp]["links"].update(links)

# Collect all unique PMIDs and DOIs across all species
all_pmids = set()
all_dois = set()
for sp, refs in species_refs.items():
    all_pmids.update(refs["pmids"])
    for link in refs["links"]:
        if link.startswith("10."):
            all_dois.add(link)

print(f"Total unique PMIDs: {len(all_pmids)}")
print(f"Total unique DOIs: {len(all_dois)}")

# -------------------------------------------------------------------
# Batch fetch PubMed titles (200 IDs per request)
# -------------------------------------------------------------------
pmid_title_map = {}
pmid_list = list(all_pmids)
batch_size = 200
for i in range(0, len(pmid_list), batch_size):
    batch = pmid_list[i:i+batch_size]
    ids = ",".join(batch)
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for pmid in batch:
                if "result" in data and pmid in data["result"]:
                    title = data["result"][pmid].get("title", "")
                    pmid_title_map[pmid] = title
                else:
                    pmid_title_map[pmid] = ""
        else:
            for pmid in batch:
                pmid_title_map[pmid] = ""
    except Exception as e:
        print(f"Error fetching batch: {e}")
        for pmid in batch:
            pmid_title_map[pmid] = ""
    time.sleep(0.5)  # gentle delay between batches
    print(f"Fetched {min(i+batch_size, len(pmid_list))}/{len(pmid_list)} PMIDs")

# -------------------------------------------------------------------
# Batch fetch DOI titles via CrossRef (50 per request)
# -------------------------------------------------------------------
doi_title_map = {}
doi_list = list(all_dois)
batch_size_doi = 50
for i in range(0, len(doi_list), batch_size_doi):
    batch = doi_list[i:i+batch_size_doi]
    # CrossRef API: POST with list of DOIs
    url = "https://api.crossref.org/works"
    params = {"rows": len(batch)}
    # Use multiple queries: we can do separate requests, but simpler: one by one? 
    # Better to use filter query: https://api.crossref.org/works?filter=doi:10.1016/j.phytochem.2004.10.017,10.1016/...
    filter_query = ",".join([f"doi:{d}" for d in batch])
    url = f"https://api.crossref.org/works?filter={filter_query}"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("message", {}).get("items", []):
                doi = item.get("DOI", "")
                title = item.get("title", [""])[0] if item.get("title") else ""
                if doi:
                    doi_title_map[doi] = title
        # For any DOI not returned, set empty
        for doi in batch:
            if doi not in doi_title_map:
                doi_title_map[doi] = ""
    except Exception as e:
        print(f"Error fetching DOI batch: {e}")
        for doi in batch:
            doi_title_map[doi] = ""
    time.sleep(0.5)
    print(f"Fetched {min(i+batch_size_doi, len(doi_list))}/{len(doi_list)} DOIs")

# -------------------------------------------------------------------
# Check each species' references
# -------------------------------------------------------------------
print("\nChecking references against species names...\n")
mismatches = []

for species, refs in species_refs.items():
    species_lower = species.lower()
    genus = species.split()[0].lower() if " " in species else species_lower
    
    for pmid in refs["pmids"]:
        title = pmid_title_map.get(pmid, "")
        if title:
            title_lower = title.lower()
            if species_lower in title_lower or genus in title_lower:
                print(f"✅ {species} – PMID {pmid} OK")
            else:
                print(f"⚠️ {species} – PMID {pmid} may be wrong: {title[:60]}...")
                mismatches.append((species, "PMID", pmid, title))
        else:
            print(f"❌ {species} – Could not fetch PMID {pmid}")
    
    for link in refs["links"]:
        if link.startswith("10."):
            title = doi_title_map.get(link, "")
            if title:
                title_lower = title.lower()
                if species_lower in title_lower or genus in title_lower:
                    print(f"✅ {species} – DOI {link} OK")
                else:
                    print(f"⚠️ {species} – DOI {link} may be wrong: {title[:60]}...")
                    mismatches.append((species, "DOI", link, title))
            else:
                print(f"❌ {species} – Could not fetch DOI {link}")
        else:
            # Not a DOI – cannot auto-check
            pass

# -------------------------------------------------------------------
# Save mismatch report
# -------------------------------------------------------------------
if mismatches:
    print(f"\n📝 Found {len(mismatches)} potential mismatches.")
    with open("reference_mismatches.csv", "w", encoding="utf-8") as f:
        f.write("Species,Type,Identifier,Title\n")
        for sp, typ, ident, title in mismatches:
            f.write(f'"{sp}",{typ},"{ident}","{title}"\n')
    print("Saved details to reference_mismatches.csv")
else:
    print("\n✅ All checked references mention their respective species.")