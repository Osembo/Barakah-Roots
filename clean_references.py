import pandas as pd
import requests
import time
import re
from urllib.parse import quote

# Load original file
df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")

def parse_species(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(";")]

# We'll build a new DataFrame with cleaned references
new_rows = []

# Cache for PMID and DOI info
pmid_cache = {}
doi_cache = {}

def get_pmid_title(pmid):
    if pmid in pmid_cache:
        return pmid_cache[pmid]
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data and pmid in data["result"]:
                title = data["result"][pmid].get("title", "")
                pmid_cache[pmid] = title
                return title
    except:
        pass
    pmid_cache[pmid] = ""
    return ""

def get_doi_title(doi):
    if doi in doi_cache:
        return doi_cache[doi]
    url = f"https://doi.org/{quote(doi)}"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            title = data.get("title", [""])[0] if data.get("title") else ""
            doi_cache[doi] = title
            return title
    except:
        pass
    doi_cache[doi] = ""
    return ""

# Process each row
for idx, row in df.iterrows():
    species_list = parse_species(row["Species"])
    if not species_list:
        # If no species, keep row as is? Probably skip.
        continue
    
    # Original PMIDs and Links
    orig_pmids = []
    if pd.notna(row["PMIDs"]):
        orig_pmids = [p.strip() for p in str(row["PMIDs"]).split(";") if p.strip()]
    orig_links = []
    if pd.notna(row["Links"]):
        orig_links = [l.strip() for l in str(row["Links"]).split(";") if l.strip()]
    
    # Cleaned lists
    good_pmids = []
    good_links = []
    
    # For each species in this row, we need to keep only references that mention the genus of at least one species?
    # Actually, the reference belongs to the entire row (all species listed). We'll keep if it matches ANY species in the row.
    # To avoid over‑filtering, we'll keep a reference if its title mentions the genus of any species in the row.
    
    genera_in_row = set()
    for sp in species_list:
        genus = sp.split()[0] if " " in sp else sp
        genera_in_row.add(genus.lower())
    
    # Check each PMID
    for pmid in orig_pmids:
        title = get_pmid_title(pmid)
        if title:
            title_lower = title.lower()
            # Keep if any genus appears in title
            if any(genus in title_lower for genus in genera_in_row):
                good_pmids.append(pmid)
            else:
                print(f"Removing PMID {pmid} for {species_list}: title doesn't mention {genera_in_row}")
        else:
            print(f"Removing invalid PMID {pmid} for {species_list}")
    
    # Check each link (only DOIs)
    for link in orig_links:
        if link.startswith("10."):
            title = get_doi_title(link)
            if title:
                title_lower = title.lower()
                if any(genus in title_lower for genus in genera_in_row):
                    good_links.append(link)
                else:
                    print(f"Removing DOI {link} for {species_list}: title doesn't mention {genera_in_row}")
            else:
                print(f"Removing invalid DOI {link} for {species_list}")
        else:
            # Non‑DOI links: we can't verify easily; keep them? Risk of junk. We'll keep but log.
            good_links.append(link)
    
    # Build new row
    new_row = row.to_dict()
    new_row["PMIDs"] = "; ".join(good_pmids) if good_pmids else ""
    new_row["Links"] = "; ".join(good_links) if good_links else ""
    # Optionally clear References text (often redundant)
    new_row["References"] = ""   # We'll rely on PMIDs/Links only
    new_rows.append(new_row)
    
    # Be nice to APIs
    time.sleep(0.2)

# Create new DataFrame and save
new_df = pd.DataFrame(new_rows)
new_df.to_excel("kenyan_compounds_cleaned.xlsx", index=False, sheet_name="molecules (1)")
print("Saved cleaned file: kenyan_compounds_cleaned.xlsx")