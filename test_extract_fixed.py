import requests
from bs4 import BeautifulSoup
import re

def extract_section_text(soup, heading_text):
    """Extract all text following a heading until next heading, including text nodes."""
    heading = None
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        if heading_text.lower() in h.get_text(strip=True).lower():
            heading = h
            break
    if not heading:
        return []
    
    results = []
    # Iterate over all next siblings (including text nodes)
    for sibling in heading.next_siblings:
        # Stop at next heading
        if hasattr(sibling, 'name') and sibling.name and sibling.name[0] == 'h':
            break
        # Skip reference divs (class="ref")
        if hasattr(sibling, 'name') and sibling.name == 'div' and sibling.get('class') and 'ref' in sibling.get('class'):
            continue
        # Handle text nodes
        if isinstance(sibling, str):
            text = sibling.strip()
            if text and len(text) > 10:
                # Remove reference numbers like [418]
                text = re.sub(r'\[\d+\]', '', text)
                results.append(text)
        # Handle tag nodes (but skip <br> as it doesn't contain text)
        elif sibling.name != 'br':
            text = sibling.get_text(strip=True)
            if text and len(text) > 10:
                text = re.sub(r'\[\d+\]', '', text)
                results.append(text)
    return results

# Test with Warburgia ugandensis
url = "https://tropical.theferns.info/viewtropical.php?id=Warburgia+ugandensis"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

medicinal = extract_section_text(soup, "Medicinal")
print("Medicinal uses found:", len(medicinal))
for i, text in enumerate(medicinal, 1):
    print(f"{i}. {text[:300]}...")