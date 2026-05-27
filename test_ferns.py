import requests
from bs4 import BeautifulSoup
import json
import re

def get_section_text(soup, heading_keywords):
    results = []
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        h_text = h.get_text(strip=True).lower()
        for kw in heading_keywords:
            if kw.lower() in h_text:
                for sibling in h.find_next_siblings():
                    if sibling.name and sibling.name[0] == 'h':
                        break
                    if sibling.name == 'p':
                        text = sibling.get_text(strip=True)
                        if text:
                            results.append(text)
                    elif sibling.name == 'ul':
                        for li in sibling.find_all('li'):
                            text = li.get_text(strip=True)
                            if text:
                                results.append(text)
                return results
    return []

def scrape_test(species_name):
    url = f"https://tropical.theferns.info/viewtropical.php?id={species_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code != 200:
        print("Page not found")
        return
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    print(f"\n--- HEADINGS FOUND ON PAGE ---")
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        print(f"{h.name}: {h.get_text(strip=True)}")
    
    print(f"\n--- EXTRACTED DATA ---")
    data = {}
    data["medicinal_uses"] = get_section_text(soup, ["Medicinal", "Medicinal Uses", "Medicinal use"])
    data["edible_uses"] = get_section_text(soup, ["Edible", "Edible Uses", "Edible use"])
    data["other_uses"] = get_section_text(soup, ["Other Uses", "Other use"])
    data["hazards"] = get_section_text(soup, ["Hazards", "Known Hazards"])
    
    for key, value in data.items():
        print(f"\n{key}:")
        for item in value:
            print(f"  - {item[:200]}...")

if __name__ == "__main__":
    scrape_test("Warburgia ugandensis")