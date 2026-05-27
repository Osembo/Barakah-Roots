import requests
import os
import pandas as pd
import time
from tqdm import tqdm

# Load species
df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")

def parse_species(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(";")]

all_species = set()
for species_str in df["Species"].dropna():
    all_species.update(parse_species(species_str))

print(f"Found {len(all_species)} unique plant species")

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_inaturalist_image_url(species_name):
    """Get the first good image URL from iNaturalist observations."""
    # Step 1: Get taxon ID for the species
    taxon_url = "https://api.inaturalist.org/v1/taxa"
    taxon_params = {"q": species_name, "per_page": 1, "only_id": True}
    try:
        taxon_resp = requests.get(taxon_url, params=taxon_params, headers=HEADERS, timeout=15)
        taxon_data = taxon_resp.json()
        if not taxon_data.get("results"):
            return None
        taxon_id = taxon_data["results"][0]["id"]
        
        # Step 2: Get observations with photos
        obs_url = "https://api.inaturalist.org/v1/observations"
        obs_params = {
            "taxon_id": taxon_id,
            "per_page": 1,
            "quality_grade": "research",
            "photo_license": "cc-by-nc"
        }
        obs_resp = requests.get(obs_url, params=obs_params, headers=HEADERS, timeout=15)
        obs_data = obs_resp.json()
        if obs_data.get("results") and obs_data["results"][0].get("photos"):
            # Get the largest available image (original)
            photo = obs_data["results"][0]["photos"][0]
            url = photo.get("url") or photo.get("original_url")
            if url:
                # Replace square/medium with original if needed
                url = url.replace("/square.", "/original.").replace("/medium.", "/original.")
                return url
    except Exception as e:
        print(f"iNaturalist error for {species_name}: {e}")
    return None

def download_image(url, species_name, image_index=1):
    safe_name = species_name.replace("/", "_").replace("\\", "_")
    species_dir = os.path.join("plant_images", safe_name)
    os.makedirs(species_dir, exist_ok=True)
    ext = os.path.splitext(url.split("?")[0])[1]
    if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif']:
        ext = '.jpg'
    filename = f"image_{image_index}{ext}"
    filepath = os.path.join(species_dir, filename)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed for {species_name}: {e}")
        return False

print("Starting iNaturalist image download...")
downloaded = 0
skipped = 0

for species in tqdm(sorted(all_species)):
    safe_name = species.replace("/", "_").replace("\\", "_")
    species_dir = os.path.join("plant_images", safe_name)
    if os.path.exists(species_dir) and any(f.startswith("image_") for f in os.listdir(species_dir)):
        skipped += 1
        continue
    img_url = get_inaturalist_image_url(species)
    if img_url:
        if download_image(img_url, species, 1):
            downloaded += 1
            print(f"✓ Downloaded for {species}")
        else:
            print(f"✗ Failed download for {species}")
    else:
        print(f"✗ No image found for {species}")
    time.sleep(0.5)

print(f"\n✅ Done. Downloaded {downloaded} new images. Skipped {skipped} species with existing images.")