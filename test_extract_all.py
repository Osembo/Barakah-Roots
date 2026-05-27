import requests
from bs4 import BeautifulSoup
import re

url = "https://tropical.theferns.info/viewtropical.php?id=Warburgia+ugandensis"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

heading = soup.find("h3", string="Medicinal")
if heading:
    text_parts = []
    for sibling in heading.next_siblings:
        # Stop at next heading
        if hasattr(sibling, 'name') and sibling.name and sibling.name[0] == 'h':
            break
        # Skip reference divs
        if hasattr(sibling, 'name') and sibling.name == 'div' and sibling.get('class') and 'ref' in sibling.get('class'):
            continue
        # Skip <br> tags (they don't contain text)
        if hasattr(sibling, 'name') and sibling.name == 'br':
            continue
        # For NavigableString (text nodes)
        if isinstance(sibling, str):
            text = sibling.strip()
            if text:
                # Remove reference numbers like [364]
                text = re.sub(r'\[\d+\]', '', text)
                # Remove trailing commas and spaces
                text = re.sub(r'^[,;\s]+|[,;\s]+$', '', text)
                if text:
                    text_parts.append(text)
    
    print(f"Found {len(text_parts)} paragraphs")
    for i, para in enumerate(text_parts, 1):
        print(f"\n--- Paragraph {i} ---")
        print(para[:300])