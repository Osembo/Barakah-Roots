import requests
from bs4 import BeautifulSoup
import re

url = "https://tropical.theferns.info/viewtropical.php?id=Warburgia+ugandensis"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

heading = soup.find("h3", string="Medicinal")
if heading:
    paragraphs = []
    current_para = []
    
    for sibling in heading.next_siblings:
        # Stop at next heading
        if hasattr(sibling, 'name') and sibling.name and sibling.name[0] == 'h':
            break
        # Skip reference divs (they contain numbers and links)
        if hasattr(sibling, 'name') and sibling.name == 'div' and sibling.get('class') and 'ref' in sibling.get('class'):
            continue
        # Handle <br> as paragraph separator
        if hasattr(sibling, 'name') and sibling.name == 'br':
            if current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
            continue
        # Handle text nodes (NavigableString)
        if isinstance(sibling, str):
            text = sibling.strip()
            if text:
                # Remove reference numbers like [364], [418]
                text = re.sub(r'\[\d+\]', '', text)
                # Remove leading/trailing punctuation that might be left
                text = re.sub(r'^[,;\s]+|[,;\s]+$', '', text)
                if text:
                    current_para.append(text)
        # Handle other tags that might contain text (like <p>)
        elif hasattr(sibling, 'name') and sibling.name in ['p', 'div']:
            # Skip if it's a reference div (already handled)
            if sibling.get('class') and 'ref' in sibling.get('class'):
                continue
            text = sibling.get_text(strip=True)
            if text:
                text = re.sub(r'\[\d+\]', '', text)
                if text:
                    current_para.append(text)
    
    # Add the last paragraph if any
    if current_para:
        paragraphs.append(' '.join(current_para))
    
    print(f"Found {len(paragraphs)} paragraphs")
    for i, para in enumerate(paragraphs, 1):
        print(f"\n--- Paragraph {i} ---")
        print(para)