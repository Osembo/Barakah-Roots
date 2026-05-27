import requests
from bs4 import BeautifulSoup

url = "https://tropical.theferns.info/viewtropical.php?id=Warburgia+ugandensis"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

# Find the Medicinal heading
med_heading = soup.find("h3", string="Medicinal")
if med_heading:
    print("Found heading: 'Medicinal'")
    print("\n--- Next 5 siblings (HTML) ---")
    count = 0
    for sibling in med_heading.find_next_siblings():
        if count >= 5:
            break
        print(f"\n--- Sibling {count+1} ---")
        print(sibling.prettify()[:500])
        count += 1
else:
    print("Medicinal heading not found")