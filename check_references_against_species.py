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

# -------------------------------------------------------------------
# Fetch title for a PMID (PubMed)
# -------------------------------------------------------------------
def get_pmid_info(pmid):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data and pmid in data["result"]:
                title = data["result"][pmid].get("title", "")
                return title
    except:
        pass
    return None

# -------------------------------------------------------------------
# Fetch title for a DOI (CrossRef)
# -------------------------------------------------------------------
def get_doi_title(doi):
    url = f"https://doi.org/{quote(doi)}"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", [""])[0] if data.get("title") else ""
            return title
    except:
        pass
    return None

# -------------------------------------------------------------------
# Check each species' references
# -------------------------------------------------------------------
print("Checking references against species names...\n")
mismatches = []

for species, refs in species_refs.items():
    species_lower = species.lower()
    genus = species.split()[0].lower() if " " in species else species_lower
    
    for pmid in refs["pmids"]:
        title = get_pmid_info(pmid)
        if title:
            title_lower = title.lower()
            if species_lower in title_lower or genus in title_lower:
                print(f"✅ {species} – PMID {pmid} mentions species/genus")
            else:
                print(f"⚠️ {species} – PMID {pmid} does NOT mention species/genus: {title[:80]}...")
                mismatches.append((species, "PMID", pmid, title))
        else:
            print(f"❌ {species} – Could not fetch PMID {pmid}")
        time.sleep(0.34)
    
    for link in refs["links"]:
        if link.startswith("10."):
            title = get_doi_title(link)
            if title:
                title_lower = title.lower()
                if species_lower in title_lower or genus in title_lower:
                    print(f"✅ {species} – DOI {link} mentions species/genus")
                else:
                    print(f"⚠️ {species} – DOI {link} does NOT mention species/genus: {title[:80]}...")
                    mismatches.append((species, "DOI", link, title))
            else:
                print(f"❌ {species} – Could not fetch DOI {link}")
        else:
            # Not a DOI, can't check automatically
            pass
        time.sleep(0.5)

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