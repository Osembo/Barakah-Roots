import pandas as pd
import requests
import time
from urllib.parse import quote

# Load original file
df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")

def parse_species(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(";")]

# Collect all unique PMIDs and DOIs across all rows
all_pmids = set()
all_dois = set()
for _, row in df.iterrows():
    if pd.notna(row["PMIDs"]):
        for p in str(row["PMIDs"]).split(";"):
            p = p.strip()
            if p.isdigit():
                all_pmids.add(p)
    if pd.notna(row["Links"]):
        for l in str(row["Links"]).split(";"):
            l = l.strip()
            if l.startswith("10."):
                all_dois.add(l)

print(f"Total unique PMIDs: {len(all_pmids)}")
print(f"Total unique DOIs: {len(all_dois)}")

# -------------------------------------------------------------------
# Batch fetch PMID titles (PubMed)
# -------------------------------------------------------------------
pmid_title = {}
pmid_list = list(all_pmids)
batch_size = 200
for i in range(0, len(pmid_list), batch_size):
    batch = pmid_list[i:i+batch_size]
    ids = ",".join(batch)
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        for pmid in batch:
            if "result" in data and pmid in data["result"]:
                pmid_title[pmid] = data["result"][pmid].get("title", "")
            else:
                pmid_title[pmid] = ""
    else:
        for pmid in batch:
            pmid_title[pmid] = ""
    print(f"Fetched {min(i+batch_size, len(pmid_list))}/{len(pmid_list)} PMIDs")
    time.sleep(0.5)

# -------------------------------------------------------------------
# Batch fetch DOI titles (CrossRef)
# -------------------------------------------------------------------
doi_title = {}
doi_list = list(all_dois)
batch_size_doi = 50
for i in range(0, len(doi_list), batch_size_doi):
    batch = doi_list[i:i+batch_size_doi]
    # Build filter query: doi:10.1016/...,doi:10.1021/...
    filter_str = ",".join([f"doi:{d}" for d in batch])
    url = f"https://api.crossref.org/works?filter={filter_str}"
    resp = requests.get(url, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get("message", {}).get("items", []):
            doi = item.get("DOI", "")
            title = item.get("title", [""])[0] if item.get("title") else ""
            if doi:
                doi_title[doi] = title
    # Fill missing
    for doi in batch:
        if doi not in doi_title:
            doi_title[doi] = ""
    print(f"Fetched {min(i+batch_size_doi, len(doi_list))}/{len(doi_list)} DOIs")
    time.sleep(0.5)

# -------------------------------------------------------------------
# Clean each row
# -------------------------------------------------------------------
new_rows = []
for idx, row in df.iterrows():
    species_list = parse_species(row["Species"])
    if not species_list:
        continue
    
    # Get genera from all species in this row
    genera = set()
    for sp in species_list:
        genus = sp.split()[0] if " " in sp else sp
        genera.add(genus.lower())
    
    # Filter PMIDs
    good_pmids = []
    if pd.notna(row["PMIDs"]):
        for p in str(row["PMIDs"]).split(";"):
            p = p.strip()
            if p.isdigit():
                title = pmid_title.get(p, "")
                if title:
                    title_lower = title.lower()
                    if any(g in title_lower for g in genera):
                        good_pmids.append(p)
                    else:
                        print(f"Removing PMID {p} for {species_list[0]}: no genus match")
                else:
                    print(f"Removing invalid PMID {p} for {species_list[0]}")
    
    # Filter DOIs
    good_dois = []
    if pd.notna(row["Links"]):
        for l in str(row["Links"]).split(";"):
            l = l.strip()
            if l.startswith("10."):
                title = doi_title.get(l, "")
                if title:
                    title_lower = title.lower()
                    if any(g in title_lower for g in genera):
                        good_dois.append(l)
                    else:
                        print(f"Removing DOI {l} for {species_list[0]}: no genus match")
                else:
                    print(f"Removing invalid DOI {l} for {species_list[0]}")
            else:
                # Non‑DOI links: keep as is (URLs)
                good_dois.append(l)
    
    # Build new row
    new_row = row.to_dict()
    new_row["PMIDs"] = "; ".join(good_pmids) if good_pmids else ""
    new_row["Links"] = "; ".join(good_dois) if good_dois else ""
    new_row["References"] = ""   # optional: clear text
    new_rows.append(new_row)

new_df = pd.DataFrame(new_rows)
new_df.to_excel("kenyan_compounds_cleaned.xlsx", index=False, sheet_name="molecules (1)")
print("\n✅ Saved cleaned file: kenyan_compounds_cleaned.xlsx")