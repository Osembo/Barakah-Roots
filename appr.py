import streamlit as st
import pandas as pd
import os
import shutil
import re
import json
from typing import List

st.set_page_config(page_title="Barakah roots", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    .plant-title {
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        color: #2c5e2e;
    }
    .section-heading {
        font-size: 1.5rem;
        font-weight: 500;
        margin-top: 1.2rem;
        margin-bottom: 0.8rem;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #ddd;
        color: #1a4d1c;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")
    df = df.dropna(subset=["Compound Name"])
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ File 'kenyan_compounds.xlsx' not found. Please place it in the same folder.")
    st.stop()

def parse_species(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(";")]

expanded_rows = []
for _, row in df.iterrows():
    for sp in parse_species(row["Species"]):
        expanded_rows.append({
            "species": sp,
            "compound": row["Compound Name"],
            "bioactivities": row["Bioactivities"] if pd.notna(row["Bioactivities"]) else "",
            "pmids": row["PMIDs"] if pd.notna(row["PMIDs"]) else "",
            "links": row["Links"] if pd.notna(row["Links"]) else "",
            "references_text": row["References"] if pd.notna(row["References"]) else "",
        })

species_df = pd.DataFrame(expanded_rows)

species_info = {}
for sp, group in species_df.groupby("species"):
    pmid_list = []
    for val in group["pmids"]:
        if pd.notna(val):
            pmid_list.extend([p.strip() for p in str(val).split(";") if p.strip()])
    
    link_list = []
    for val in group["links"]:
        if pd.notna(val):
            link_list.extend([l.strip() for l in str(val).split(";") if l.strip()])
    
    ref_text = ""
    for val in group["references_text"]:
        if pd.notna(val) and str(val).strip():
            ref_text = str(val).strip()
            break
    
    species_info[sp] = {
        "compounds": group["compound"].unique().tolist(),
        "bioactivities": "; ".join(group["bioactivities"].dropna().unique()),
        "pmids": sorted(set(pmid_list)),
        "links": sorted(set(link_list)),
        "references_text": ref_text,
    }

# Load manual references if any
MANUAL_REFS_FILE = "manual_references.json"
if os.path.exists(MANUAL_REFS_FILE):
    with open(MANUAL_REFS_FILE, "r") as f:
        manual_refs = json.load(f)
else:
    manual_refs = {}

local_names_dict = {
    "Warburgia ugandensis": ["Mwarobaini", "Pepper-bark tree"],
    "Erythrina abyssinica": ["Mutonga", "Red-hot-poker tree"],
    "Aloe secundiflora": ["Aloe vera", "Socotrine aloe"],
    "Croton megalocarpoides": ["Mukinduri", "Mukinduri tree"],
    "Terminalia brownii": ["Mwangati", "Brown terminalia"],
    "Millettia dura": ["Mubiribiri", "Mubiri"],
    "Vepris uguenensis": ["Mwafu", "Uguenensis"],
    "Zanthoxylum usambarense": ["Mkunungu", "Usambara thorn"],
}

preparation_dict = {
    "Warburgia ugandensis": "Bark is boiled in water to make a decoction. Leaves can be crushed and applied topically.",
    "Erythrina abyssinica": "Root bark is pounded and mixed with cold water for malaria. Leaves are used as a tea.",
    "Aloe secundiflora": "Leaf sap is extracted and applied directly or mixed with water for internal use.",
    "Croton megalocarpoides": "Roots are chewed or made into a decoction for stomach ailments.",
    "Terminalia brownii": "Bark is soaked in water and drunk for bacterial infections.",
    "Millettia dura": "Seeds are crushed and used as a fish poison; bark decoction for fever.",
    "Vepris uguenensis": "Leaves are steamed and inhaled for respiratory problems.",
    "Zanthoxylum usambarense": "Roots and bark are chewed or boiled for toothache and malaria.",
}

def get_local_names(species):
    if species in local_names_dict:
        return local_names_dict[species]
    genus = species.split()[0] if " " in species else species
    return [f"{genus} local", f"Wild {genus}"]

def get_preparation(species):
    return preparation_dict.get(species, "Traditionally, the plant parts are boiled in water or soaked in cold water to extract the medicinal compounds.")

def get_medicinal_uses(bio_str):
    if not bio_str or pd.isna(bio_str):
        return ["No specific medicinal uses recorded."]
    uses = []
    if "anti‑plasmodial" in bio_str or "antimalarial" in bio_str:
        uses.append("Used in traditional medicine to treat malaria and fevers.")
    if "antibacterial" in bio_str or "antimicrobial" in bio_str:
        uses.append("Effective against bacterial infections.")
    if "antifungal" in bio_str:
        uses.append("Used to treat fungal infections.")
    if "cytotoxic" in bio_str or "anticancer" in bio_str:
        uses.append("Shows potential anticancer properties.")
    if "anti‑inflammatory" in bio_str:
        uses.append("Reduces inflammation.")
    if "antioxidant" in bio_str or "radical scavenging" in bio_str:
        uses.append("Rich in antioxidants.")
    if not uses:
        uses.append("Traditional medicine, specific uses not recorded.")
    return uses

def get_other_uses(bio_str):
    other = []
    if "larvicidal" in bio_str or "insecticidal" in bio_str:
        other.append("Used as a natural insecticide or larvicide.")
    if "repellent" in bio_str:
        other.append("Acts as an insect repellent.")
    return other if other else []

os.makedirs("plant_images", exist_ok=True)

def get_species_image_dir(species_name: str) -> str:
    safe_name = species_name.replace("/", "_").replace("\\", "_")
    dir_path = os.path.join("plant_images", safe_name)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def get_manual_images(species_name: str) -> List[str]:
    dir_path = get_species_image_dir(species_name)
    if not os.path.exists(dir_path):
        return []
    exts = ('.jpg', '.jpeg', '.png', '.gif')
    files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.lower().endswith(exts)]
    return sorted(files)

def save_manual_image(species_name: str, uploaded_file) -> bool:
    dir_path = get_species_image_dir(species_name)
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
        st.error("Only JPG, PNG, GIF images are allowed.")
        return False
    existing = get_manual_images(species_name)
    next_num = len(existing) + 1
    safe_name = f"image_{next_num}{ext}"
    path = os.path.join(dir_path, safe_name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return True

def delete_manual_image(species_name: str, filename: str):
    dir_path = get_species_image_dir(species_name)
    file_path = os.path.join(dir_path, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def delete_all_images(species_name: str):
    dir_path = get_species_image_dir(species_name)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
        return True
    return False

def search_by_condition(condition):
    condition_lower = condition.lower()
    return [sp for sp, info in species_info.items() if condition_lower in info["bioactivities"].lower()]

def search_by_keyword(keyword):
    keyword_lower = keyword.lower()
    matches = []
    for sp, info in species_info.items():
        if keyword_lower in sp.lower():
            matches.append(sp)
            continue
        if any(keyword_lower in name.lower() for name in get_local_names(sp)):
            matches.append(sp)
            continue
        if keyword_lower in info["bioactivities"].lower():
            matches.append(sp)
            continue
        for comp in info["compounds"]:
            if keyword_lower in comp.lower():
                matches.append(sp)
                break
    return matches

ADMIN_PASSWORD = "admin123"

with st.sidebar:
    st.markdown("---")
    if st.checkbox("🔐 Admin login"):
        password = st.text_input("Password", type="password")
        if password == ADMIN_PASSWORD:
            st.success("Logged in as admin")
            
            # ---------- Image Management ----------
            st.subheader("🖼️ Manage Plant Images")
            species_list = sorted(species_info.keys())
            selected_species_admin = st.selectbox("Select plant species", species_list)
            
            existing_images = get_manual_images(selected_species_admin)
            if existing_images:
                st.write(f"**{len(existing_images)} image(s) stored**")
                cols = st.columns(min(3, len(existing_images)))
                for idx, img_path in enumerate(existing_images):
                    with cols[idx % 3]:
                        st.image(img_path, use_container_width=True)
                        filename = os.path.basename(img_path)
                        if st.button(f"🗑️ Delete {filename}", key=f"del_{selected_species_admin}_{idx}"):
                            if delete_manual_image(selected_species_admin, filename):
                                st.success(f"Deleted {filename}")
                                st.rerun()
                if st.button("🔥 Delete ALL images for this plant"):
                    if delete_all_images(selected_species_admin):
                        st.success("All images deleted")
                        st.rerun()
            else:
                st.info("No manual images yet.")
            
            st.write("**Add new image(s)**")
            uploaded_files = st.file_uploader(
                "Choose image(s) (JPG, PNG, GIF)",
                type=["jpg", "jpeg", "png", "gif"],
                accept_multiple_files=True
            )
            if uploaded_files and st.button("💾 Save selected images"):
                saved = 0
                for file in uploaded_files:
                    if save_manual_image(selected_species_admin, file):
                        saved += 1
                if saved:
                    st.success(f"Saved {saved} new image(s)")
                    st.rerun()
                else:
                    st.error("No valid images saved.")
            
            # ---------- Reference Editor ----------
            st.divider()
            st.subheader("📝 Edit Scientific References")
            ref_plant = st.selectbox("Select plant to edit references", species_list, key="ref_plant")
            
            # Show current data from Excel
            current_pmids = species_info[ref_plant]["pmids"]
            current_links = species_info[ref_plant]["links"]
            current_text = species_info[ref_plant]["references_text"]
            st.write("**Current data from Excel:**")
            if current_pmids:
                st.write(f"PMIDs: {', '.join(current_pmids)}")
            if current_links:
                st.write(f"Links: {', '.join(current_links)}")
            if current_text:
                st.write(f"Article titles: {current_text[:200]}...")
            
            # Show existing manual references if any
            if ref_plant in manual_refs and manual_refs[ref_plant]:
                st.write("**Current manual references:**")
                for r in manual_refs[ref_plant]:
                    st.write(f"- {r}")
            
            # Input for new manual references
            manual_refs_input = st.text_area(
                "Enter one reference per line (URLs, DOIs, or free text)",
                height=150,
                key="manual_refs_area",
                help="Example:\nhttps://pubmed.ncbi.nlm.nih.gov/12345678/\n10.1016/j.phytochem.2004.10.017\nA traditional herbal medicine..."
            )
            
            if st.button("💾 Save Manual References", key="save_refs_btn"):
                # Save to manual_refs.json
                ref_list = [line.strip() for line in manual_refs_input.split("\n") if line.strip()]
                manual_refs[ref_plant] = ref_list
                with open(MANUAL_REFS_FILE, "w") as f:
                    json.dump(manual_refs, f, indent=2)
                st.success(f"Saved {len(ref_list)} references for {ref_plant}")
                st.rerun()
            
            # Option to clear manual references for this plant
            if ref_plant in manual_refs and manual_refs[ref_plant]:
                if st.button("🗑️ Clear Manual References for this plant"):
                    del manual_refs[ref_plant]
                    with open(MANUAL_REFS_FILE, "w") as f:
                        json.dump(manual_refs, f, indent=2)
                    st.success("Cleared")
                    st.rerun()
        elif password:
            st.error("Wrong password")

st.title("🌱 Barakah roots")
st.markdown("Search for medicinal plants of Kenya by **health condition** or **keyword**.")

col1, col2 = st.columns(2)

with col1:
    condition_list = [
        "anti‑plasmodial", "antimalarial",
        "antibacterial", "antifungal",
        "cytotoxic", "anti‑inflammatory",
        "antioxidant", "antileishmanial"
    ]
    selected_condition = st.selectbox("🔍 Search by condition", [""] + condition_list)
    if selected_condition:
        results = search_by_condition(selected_condition)

with col2:
    keyword = st.text_input("🔎 Search by keyword", placeholder="e.g., malaria, Mwarobaini, fever, bark")
    if keyword:
        results = search_by_keyword(keyword)

if 'results' not in locals():
    results = []
    st.info("👈 Select a condition or type a keyword to start.")

if results:
    st.subheader(f"🌿 {len(results)} plant(s) found")
    selected_plant = st.selectbox("Click to view plant profile", results)

    if selected_plant:
        info = species_info[selected_plant]
        local_names = get_local_names(selected_plant)
        medicinal_uses = get_medicinal_uses(info["bioactivities"])
        other_uses = get_other_uses(info["bioactivities"])
        preparation = get_preparation(selected_plant)

        st.divider()
        
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown(f'<div class="plant-title">{selected_plant}</div>', unsafe_allow_html=True)
            st.markdown(f"**Common names:** {', '.join(local_names)}")
            st.markdown(f"**Preparation method:** {preparation}")
        with col_right:
            manual_images = get_manual_images(selected_plant)
            if manual_images:
                st.image(manual_images[0], use_container_width=True)
                if len(manual_images) > 1:
                    thumb_cols = st.columns(min(3, len(manual_images)-1))
                    for i, img_path in enumerate(manual_images[1:4]):
                        with thumb_cols[i % 3]:
                            st.image(img_path, use_container_width=True)
            else:
                st.image("https://placehold.co/400x300?text=No+image+uploaded", use_container_width=True)
                st.caption("Add images via admin panel")
        
        st.markdown('<div class="section-heading">🌿 Medicinal Uses</div>', unsafe_allow_html=True)
        for use in medicinal_uses:
            st.markdown(f"- {use}")
        
        st.markdown('<div class="section-heading">🔬 Active Compounds</div>', unsafe_allow_html=True)
        if info["compounds"]:
            for comp in info["compounds"][:15]:
                st.markdown(f"- {comp}")
            if len(info["compounds"]) > 15:
                st.caption(f"... and {len(info['compounds']) - 15} more compounds.")
        else:
            st.info("No specific compounds recorded in the dataset.")
        
        if other_uses:
            st.markdown('<div class="section-heading">🌾 Other Uses</div>', unsafe_allow_html=True)
            for use in other_uses:
                st.markdown(f"- {use}")
        
        # ---------- Scientific References (manual overrides first) ----------
        st.markdown('<div class="section-heading">📚 Scientific References</div>', unsafe_allow_html=True)
        
        if selected_plant in manual_refs and manual_refs[selected_plant]:
            # Show manually entered references
            for ref in manual_refs[selected_plant]:
                if ref.startswith(('http://', 'https://')):
                    st.markdown(f"- [Link]({ref})")
                elif ref.startswith("10."):
                    st.markdown(f"- [DOI {ref}](https://doi.org/{ref})")
                else:
                    st.markdown(f"- {ref}")
        else:
            # Fallback to Excel data
            ref_links = []
            for pmid in info["pmids"]:
                if pmid.isdigit():
                    ref_links.append(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            for link in info["links"]:
                link = link.strip()
                if link.startswith(('http://', 'https://')):
                    ref_links.append(link)
                elif link.startswith("10."):
                    ref_links.append(f"https://doi.org/{link}")
            unique_refs = []
            for ref in ref_links:
                if ref not in unique_refs:
                    unique_refs.append(ref)
            if unique_refs:
                for ref in unique_refs:
                    if "pubmed" in ref:
                        label = f"PubMed {ref.split('/')[-1]}"
                    elif "doi.org" in ref:
                        label = f"DOI {ref.split('doi.org/')[-1][:50]}"
                    else:
                        label = "Reference"
                    st.markdown(f"- [{label}]({ref})")
            elif info["references_text"]:
                st.markdown("**Source titles (from dataset):**")
                refs = re.split(r'[;\n]+', info["references_text"])
                for ref in refs[:5]:
                    ref = ref.strip()
                    if ref:
                        if len(ref) > 150:
                            ref = ref[:147] + "..."
                        st.markdown(f"- {ref}")
            else:
                st.info("No references available. Use admin panel to add manual references.")
        
        if st.button("← New search"):
            st.rerun()

elif (selected_condition or keyword) and not results:
    st.warning("No plants found. Try a different keyword or condition.")

st.divider()
st.caption("Barakah roots – Kenyan medicinal plant knowledge. Data from scientific literature. Add your own images and correct references via admin panel.")