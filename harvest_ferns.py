import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import os
import re

# Load species from Excel
df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")

def parse_species(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(";")]

all_species = set()
for species_str in df["Species"].dropna():
    all_species.update(parse_species(species_str))

print(f"Found {len(all_species)} unique plant species")

# Load existing cache
cache_file = "ferns_cache.json"
if os.path.exists(cache_file):
    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

headers = {"User-Agent": "Mozilla/5.0"}

def extract_section(soup, heading_text):
    heading = None
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        if heading_text.lower() in h.get_text(strip=True).lower():
            heading = h
            break
    if not heading:
        return []
    full_text = ""
    for sibling in heading.next_siblings:
        if hasattr(sibling, 'name') and sibling.name and sibling.name[0] == 'h':
            break
        if hasattr(sibling, 'name') and sibling.name == 'div' and sibling.get('class') and 'ref' in sibling.get('class'):
            continue
        text = sibling.get_text(strip=True) if hasattr(sibling, 'get_text') else str(sibling).strip()
        if text:
            full_text += " " + text
    full_text = re.sub(r'\[\d+\]', '', full_text)
    full_text = re.sub(r'Title.*?Description.*?\.', '', full_text, flags=re.DOTALL)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    paragraphs = [p.strip() + '.' for p in full_text.split('. ') if len(p.strip()) > 20]
    return paragraphs

def scrape_ferns(species_name):
    url = f"https://tropical.theferns.info/viewtropical.php?id={species_name.replace(' ', '+')}"
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        data = {
            "common_names": [],
            "medicinal_uses": [],
            "edible_uses": [],
            "other_uses": [],
            "hazards": [],
            "image_urls": []
        }
        # Common names
        common_name_text = soup.find(string=re.compile(r"Common Name:", re.I))
        if common_name_text:
            parent = common_name_text.find_parent()
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem and next_elem.name == 'p':
                    names = next_elem.get_text(strip=True)
                    for name in re.split(r'[,;\n]', names):
                        name = name.strip()
                        if name:
                            data["common_names"].append(name)
        data["medicinal_uses"] = extract_section(soup, "Medicinal")
        data["edible_uses"] = extract_section(soup, "Edible")
        data["other_uses"] = extract_section(soup, "Other Uses")
        data["hazards"] = extract_section(soup, "Hazards")
        # Images
        gallery = soup.find("div", class_="imagegallery") or soup.find("div", id="ImageGallery")
        if gallery:
            for img in gallery.find_all("img"):
                src = img.get("src")
                if src and not src.startswith("data:") and "banana.png" not in src and "medi.png" not in src:
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        src = "https://tropical.theferns.info" + src
                    data["image_urls"].append(src)
        if not any(len(v) > 0 for v in data.values()):
            return None
        return data
    except Exception as e:
        print(f"Error {species_name}: {e}")
        return None

# Test one species
print("\nTesting Warburgia ugandensis...")
test_result = scrape_ferns("Warburgia ugandensis")
if test_result:
    print("Medicinal uses:")
    for use in test_result["medicinal_uses"][:3]:
        print(f"  - {use[:200]}")
    cache["Warburgia ugandensis"] = test_result
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print("\nSaved to ferns_cache.json")
else:
    print("Failed")