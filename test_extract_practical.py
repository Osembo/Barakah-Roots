import requests
from bs4 import BeautifulSoup
import re

url = "https://tropical.theferns.info/viewtropical.php?id=Warburgia+ugandensis"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

heading = soup.find("h3", string="Medicinal")
if heading:
    # Collect all text from siblings until next heading
    full_text = ""
    for sibling in heading.next_siblings:
        if hasattr(sibling, 'name') and sibling.name and sibling.name[0] == 'h':
            break
        # Skip reference divs
        if hasattr(sibling, 'name') and sibling.name == 'div' and sibling.get('class') and 'ref' in sibling.get('class'):
            continue
        # Get text from the sibling (including text nodes via get_text)
        text = sibling.get_text(strip=True) if hasattr(sibling, 'get_text') else str(sibling).strip()
        if text:
            full_text += " " + text
    
    # Clean up: remove reference numbers like [364], [418]
    full_text = re.sub(r'\[\d+\]', '', full_text)
    # Split into sentences (by period followed by space or newline)
    sentences = [s.strip() for s in full_text.split('. ') if len(s.strip()) > 20]
    
    print(f"Found {len(sentences)} sentences/paragraphs")
    for i, sent in enumerate(sentences[:5], 1):
        print(f"\n{i}. {sent}.")