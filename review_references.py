import pandas as pd
import requests
import time
import re
from urllib.parse import quote

# -------------------------------------------------------------------
# Load Excel
# -------------------------------------------------------------------
df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")
df = df.dropna(subset=["Compound Name"])

# Extract unique PMIDs and Links (split by semicolon)
all_pmids = set()
all_links = set()
all_ref_texts = []

for _, row in df.iterrows():
    pmids = row["PMIDs"]
    if pd.notna(pmids):
        for p in str(pmids).split(";"):
            p = p.strip()
            if p.isdigit():
                all_pmids.add(p)
    links = row["Links"]
    if pd.notna(links):
        for l in str(links).split(";"):
            l = l.strip()
            if l:
                all_links.add(l)
    ref = row["References"]
    if pd.notna(ref):
        all_ref_texts.append(str(ref).strip())

print(f"Total unique PMIDs: {len(all_pmids)}")
print(f"Total unique Links/DOIs: {len(all_links)}")
print(f"Total Reference text entries: {len(all_ref_texts)}")
print("-" * 60)

# -------------------------------------------------------------------
# Check PMIDs using PubMed E-utilities
# -------------------------------------------------------------------
def check_pmid(pmid):
    """Return (valid, title) where title is from PubMed."""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data and pmid in data["result"]:
                title = data["result"][pmid].get("title", "")
                return True, title
    except:
        pass
    return False, ""

print("\n🔍 Checking PMIDs...\n")
pmid_results = {}
for pmid in sorted(all_pmids):
    valid, title = check_pmid(pmid)
    pmid_results[pmid] = {"valid": valid, "title": title}
    status = "✅" if valid else "❌"
    print(f"{status} PMID {pmid}: {title[:80] if title else 'No title / Invalid'}")
    time.sleep(0.34)  # Respect rate limit (3 requests/sec max)

# -------------------------------------------------------------------
# Check Links/DOIs (basic reachability and CrossRef title)
# -------------------------------------------------------------------
def check_link(url):
    """Check if URL is reachable (status 200). For DOIs, also get title via CrossRef."""
    if url.startswith("10."):
        # Try to resolve DOI
        doi_url = f"https://doi.org/{quote(url)}"
        headers = {"Accept": "application/json"}
        try:
            resp = requests.get(doi_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", [""])[0] if data.get("title") else ""
                return True, title
        except:
            pass
        # Fallback: just check DOI resolver
        try:
            resp = requests.head(doi_url, timeout=10)
            return resp.status_code == 200, ""
        except:
            return False, ""
    else:
        # Normal URL: check HEAD request
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)
            return resp.status_code == 200, ""
        except:
            return False, ""

print("\n🔍 Checking Links/DOIs...\n")
link_results = {}
for link in sorted(all_links):
    valid, title = check_link(link)
    link_results[link] = {"valid": valid, "title": title}
    status = "✅" if valid else "❌"
    if title:
        print(f"{status} {link[:60]}: {title[:80]}")
    else:
        print(f"{status} {link[:60]}")

# -------------------------------------------------------------------
# Compare Reference text against PMID titles
# -------------------------------------------------------------------
print("\n🔍 Matching Reference texts with PMID titles...\n")
matches = []
mismatches = []
for ref in all_ref_texts[:20]:  # Limit to first 20 for brevity
    found_match = False
    for pmid, info in pmid_results.items():
        if info["valid"] and info["title"] and info["title"].lower() in ref.lower():
            matches.append((pmid, ref[:80], info["title"][:80]))
            found_match = True
            break
    if not found_match:
        mismatches.append(ref[:100])
if matches:
    print("✅ Matches found (Reference text contains PubMed title):")
    for m in matches[:5]:
        print(f"  PMID {m[0]}: '{m[1]}...' ↔ '{m[2]}...'")
if mismatches:
    print("\n⚠️ Reference texts that do NOT match any retrieved PMID title (first 10):")
    for mm in mismatches[:10]:
        print(f"  - {mm}...")
else:
    print("All sampled Reference texts matched a PMID title.")

# -------------------------------------------------------------------
# Summary report
# -------------------------------------------------------------------
print("\n" + "=" * 60)
print("SUMMARY REPORT")
print("=" * 60)
invalid_pmids = [p for p, info in pmid_results.items() if not info["valid"]]
if invalid_pmids:
    print(f"\n❌ Invalid PMIDs ({len(invalid_pmids)}):")
    for p in invalid_pmids:
        print(f"   {p}")
else:
    print("\n✅ All PMIDs are valid.")

invalid_links = [l for l, info in link_results.items() if not info["valid"]]
if invalid_links:
    print(f"\n❌ Unreachable Links/DOIs ({len(invalid_links)}):")
    for l in invalid_links:
        print(f"   {l[:80]}")
else:
    print("\n✅ All Links/DOIs are reachable.")

print("\n💡 Suggestion: Use the admin panel in the Streamlit app to manually correct any invalid references.")