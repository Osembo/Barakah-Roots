import requests
from bs4 import BeautifulSoup

url = "https://tropical.theferns.info/viewtropical.php?id=Warburgia+ugandensis"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

heading = soup.find("h3", string="Medicinal")
print("Found heading:", heading)
if heading:
    print("\nSiblings after heading (including text nodes):")
    for i, sibling in enumerate(heading.next_siblings):
        if i > 20:
            break
        print(f"\n--- Sibling {i} ---")
        print(f"Type: {type(sibling)}")
        if hasattr(sibling, 'name'):
            print(f"Name: {sibling.name}")
            if sibling.name == 'div':
                print(f"Class: {sibling.get('class')}")
            print(f"Text (first 100): {str(sibling.get_text(strip=True))[:100]}")
        else:
            print(f"Text: {repr(sibling)[:100]}")