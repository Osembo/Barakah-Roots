import streamlit as st
import pandas as pd
import os
import shutil
import re
import json
from typing import List
import base64
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Barakah Roots",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Page background ── */
.stApp {
    background-color: #f5f0e8;
}

/* ── Hero header ── */
.hero {
    background: linear-gradient(135deg, #1a3d1e 0%, #2c5e2e 60%, #3d7a40 100%);
    border-radius: 20px;
    padding: 3rem 3rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 280px; height: 280px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.hero::after {
    content: "";
    position: absolute;
    bottom: -40px; left: 40px;
    width: 160px; height: 160px;
    background: rgba(255,255,255,0.03);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Lora', serif;
    font-size: 3rem;
    font-weight: 600;
    color: #e8f4e8;
    margin: 0 0 0.4rem;
    letter-spacing: -0.5px;
}
.hero-sub {
    font-size: 1.05rem;
    color: #a8cca8;
    font-weight: 300;
    margin: 0;
}

/* ── Search card ── */
.search-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border: 1px solid #e8e2d8;
}

/* ── Plant profile ── */
.profile-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 2rem 2.5rem;
    margin-top: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07);
    border: 1px solid #e8e2d8;
}
.plant-title {
    font-family: 'Lora', serif;
    font-size: 2rem;
    font-weight: 600;
    color: #1a3d1e;
    margin: 0 0 0.25rem;
    font-style: italic;
}
.local-name-badge {
    display: inline-block;
    background: #e8f4e8;
    color: #2c5e2e;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 0 4px 4px 0;
    border: 1px solid #c5dfc5;
}
.section-heading {
    font-family: 'Lora', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #1a3d1e;
    margin: 1.8rem 0 0.9rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #d4e8d4;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── KPI metric cards ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 1rem 0;
}
.metric-box {
    background: #f0f7f0;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
    border: 1px solid #d4e8d4;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 600;
    color: #1a3d1e;
    line-height: 1;
}
.metric-label {
    font-size: 0.75rem;
    color: #5a7a5a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 4px;
}

/* ── Compound tag chips ── */
.compound-chip {
    display: inline-block;
    background: #f5f0e8;
    color: #3d4a3d;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 0.8rem;
    margin: 3px;
    border: 1px solid #ddd5c4;
}

/* ── Activity badge ── */
.activity-badge {
    display: inline-block;
    background: #e8f4e8;
    color: #1a4d1c;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.83rem;
    font-weight: 500;
    margin: 3px;
    border: 1px solid #c5dfc5;
}

/* ── Result card (in list) ── */
.result-card {
    background: #fff;
    border-radius: 14px;
    padding: 1rem 1.4rem;
    margin-bottom: 0.7rem;
    border: 1px solid #e8e2d8;
    cursor: pointer;
    transition: box-shadow 0.2s, border-color 0.2s;
}
.result-card:hover {
    box-shadow: 0 4px 16px rgba(44,94,46,0.12);
    border-color: #b0d4b0;
}
.result-card-name {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 1.05rem;
    color: #1a3d1e;
    font-weight: 600;
}
.result-card-meta {
    font-size: 0.82rem;
    color: #7a8a7a;
    margin-top: 2px;
}

/* ── Reference link ── */
.ref-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f5f0e8;
    border: 1px solid #ddd5c4;
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 0.82rem;
    color: #2c5e2e;
    text-decoration: none;
    margin: 3px;
    font-weight: 500;
}

/* ── Sidebar override ── */
[data-testid="stSidebar"] {
    background: #1a3d1e;
}
[data-testid="stSidebar"] * {
    color: #e8f4e8 !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox select,
[data-testid="stSidebar"] .stTextArea textarea {
    background: #2c5e2e !important;
    border-color: #3d7a40 !important;
    color: #e8f4e8 !important;
}

/* ── Streamlit overrides ── */
div[data-testid="stSelectbox"] > div > div {
    background: #fff;
    border-radius: 10px;
    border-color: #d4e8d4;
}
div[data-testid="stTextInput"] > div > div > input {
    background: #fff;
    border-radius: 10px;
    border-color: #d4e8d4;
}
.stButton > button {
    background: #2c5e2e;
    color: #fff;
    border: none;
    border-radius: 10px;
    font-weight: 500;
    padding: 0.5rem 1.5rem;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #1a4d1c;
    border: none;
}

/* ── Footer ── */
.footer-bar {
    text-align: center;
    padding: 1.5rem;
    color: #8a9a8a;
    font-size: 0.82rem;
    margin-top: 3rem;
    border-top: 1px solid #e0d8cc;
}

/* ── Stats bar ── */
.stats-bar {
    display: flex;
    gap: 2rem;
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-top: 1.5rem;
}
.stat-item { text-align: center; }
.stat-num { font-size: 1.5rem; font-weight: 600; color: #c8e6c8; }
.stat-lab { font-size: 0.72rem; color: #90b490; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Quick filter chips ── */
.qf-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 10px;
    margin: 0.6rem 0 1.2rem;
}
.qf-chip {
    background: #ffffff;
    border: 1px solid #d4e8d4;
    border-radius: 14px;
    padding: 14px 8px 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    text-align: center;
    transition: box-shadow 0.15s, border-color 0.15s, background 0.15s;
}
.qf-chip:hover {
    background: #f0f7f0;
    border-color: #7aaa7a;
    box-shadow: 0 3px 12px rgba(44,94,46,0.1);
}
.qf-chip svg { display: block; }
.qf-chip-label {
    font-size: 0.72rem;
    font-weight: 500;
    color: #3a5a3a;
    line-height: 1.3;
}
</style>
""", unsafe_allow_html=True)

# ── Data loading ────────────────────────────────────────────────────────────
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

# ── Manual references ────────────────────────────────────────────────────────
MANUAL_REFS_FILE = "manual_references.json"
if os.path.exists(MANUAL_REFS_FILE):
    with open(MANUAL_REFS_FILE, "r") as f:
        manual_refs = json.load(f)
else:
    manual_refs = {}

# ── Dictionaries ─────────────────────────────────────────────────────────────
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

BIOACTIVITY_MAP = {
    "anti‑plasmodial": ("Antimalarial", "🦟"),
    "antimalarial": ("Antimalarial", "🦟"),
    "antibacterial": ("Antibacterial", "🦠"),
    "antimicrobial": ("Antimicrobial", "🦠"),
    "antifungal": ("Antifungal", "🍄"),
    "cytotoxic": ("Anticancer", "🎗️"),
    "anticancer": ("Anticancer", "🎗️"),
    "anti‑inflammatory": ("Anti-inflammatory", "🔥"),
    "antioxidant": ("Antioxidant", "⚡"),
    "radical scavenging": ("Antioxidant", "⚡"),
    "antileishmanial": ("Antileishmanial", "🧬"),
    "larvicidal": ("Larvicidal", "🪲"),
    "insecticidal": ("Insecticidal", "🪲"),
}

CHIP_SVGS = {
    "anti‑plasmodial": '<path d="M24 36 C24 36 14 26 14 18 C14 12 18.5 8 24 8 C29.5 8 34 12 34 18 C34 26 24 36 24 36Z" fill="#3d7a40" opacity="0.85"/><path d="M24 36 C24 36 16 25 17 18 C18 13 21 10 24 10" fill="#2c5e2e" opacity="0.5"/><ellipse cx="24" cy="30" rx="10" ry="5" fill="#c5dfc5" opacity="0.4"/><path d="M24 20 L20 16 M24 20 L28 15 M24 20 L24 14" stroke="#e8f4e8" stroke-width="1.2" stroke-linecap="round" opacity="0.7"/><circle cx="24" cy="37" r="2" fill="#1a3d1e" opacity="0.3"/>',
    "antimalarial":    '<path d="M24 36 C24 36 14 26 14 18 C14 12 18.5 8 24 8 C29.5 8 34 12 34 18 C34 26 24 36 24 36Z" fill="#3d7a40" opacity="0.85"/><path d="M24 36 C24 36 16 25 17 18 C18 13 21 10 24 10" fill="#2c5e2e" opacity="0.5"/><ellipse cx="24" cy="30" rx="10" ry="5" fill="#c5dfc5" opacity="0.4"/><path d="M24 20 L20 16 M24 20 L28 15 M24 20 L24 14" stroke="#e8f4e8" stroke-width="1.2" stroke-linecap="round" opacity="0.7"/>',
    "antibacterial":   '<circle cx="24" cy="24" r="9" fill="#a8cca8" opacity="0.3"/><circle cx="24" cy="24" r="5" fill="#2c5e2e" opacity="0.8"/><circle cx="24" cy="24" r="2.5" fill="#e8f4e8" opacity="0.9"/><line x1="24" y1="10" x2="24" y2="14" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="24" y1="34" x2="24" y2="38" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="10" y1="24" x2="14" y2="24" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="34" y1="24" x2="38" y2="24" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="14.1" y1="14.1" x2="17" y2="17" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="33.9" y1="14.1" x2="31" y2="17" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="31" y1="31" x2="33.9" y2="33.9" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="14.1" y1="33.9" x2="17" y2="31" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/>',
    "antimicrobial":   '<circle cx="24" cy="24" r="9" fill="#a8cca8" opacity="0.3"/><circle cx="24" cy="24" r="5" fill="#2c5e2e" opacity="0.8"/><circle cx="24" cy="24" r="2.5" fill="#e8f4e8" opacity="0.9"/><line x1="24" y1="10" x2="24" y2="14" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="24" y1="34" x2="24" y2="38" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="10" y1="24" x2="14" y2="24" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><line x1="34" y1="24" x2="38" y2="24" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/>',
    "antifungal":      '<ellipse cx="20" cy="28" rx="7" ry="9" fill="#5a8a5a" opacity="0.6" transform="rotate(-15 20 28)"/><ellipse cx="29" cy="26" rx="6" ry="8" fill="#3d7a40" opacity="0.75" transform="rotate(10 29 26)"/><ellipse cx="24" cy="32" rx="5" ry="7" fill="#2c5e2e" opacity="0.8"/><path d="M24 38 L24 42" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/><path d="M18 40 L24 42 L30 40" stroke="#1a3d1e" stroke-width="1" stroke-linecap="round"/>',
    "cytotoxic":       '<path d="M24 8 C20 8 16 12 16 17 C16 22 19 25 22 27 L22 38 L26 38 L26 27 C29 25 32 22 32 17 C32 12 28 8 24 8Z" fill="#3d7a40" opacity="0.8"/><path d="M22 38 L26 38 L25.5 42 L22.5 42Z" fill="#1a3d1e" opacity="0.6"/><path d="M16 17 C14 16 11 17 10 20" stroke="#2c5e2e" stroke-width="1.5" stroke-linecap="round" fill="none"/><path d="M32 17 C34 16 37 17 38 20" stroke="#2c5e2e" stroke-width="1.5" stroke-linecap="round" fill="none"/><ellipse cx="24" cy="16" rx="4" ry="5" fill="#e8f4e8" opacity="0.25"/>',
    "anticancer":      '<path d="M24 8 C20 8 16 12 16 17 C16 22 19 25 22 27 L22 38 L26 38 L26 27 C29 25 32 22 32 17 C32 12 28 8 24 8Z" fill="#3d7a40" opacity="0.8"/><path d="M22 38 L26 38 L25.5 42 L22.5 42Z" fill="#1a3d1e" opacity="0.6"/><path d="M16 17 C14 16 11 17 10 20" stroke="#2c5e2e" stroke-width="1.5" stroke-linecap="round" fill="none"/><path d="M32 17 C34 16 37 17 38 20" stroke="#2c5e2e" stroke-width="1.5" stroke-linecap="round" fill="none"/>',
    "anti‑inflammatory": '<path d="M24 10 C24 10 12 18 12 27 C12 33.6 17.4 39 24 39 C30.6 39 36 33.6 36 27 C36 18 24 10 24 10Z" fill="#5a8a5a" opacity="0.3"/><path d="M24 16 C24 16 16 22 16 28 C16 32.4 19.6 36 24 36 C28.4 36 32 32.4 32 28 C32 22 24 16 24 16Z" fill="#2c5e2e" opacity="0.75"/><path d="M24 22 C24 22 19 26 19 30 C19 32.8 21.2 35 24 35" stroke="#e8f4e8" stroke-width="1" fill="none" opacity="0.5"/>',
    "antioxidant":     '<circle cx="24" cy="22" r="10" fill="#a8cca8" opacity="0.25"/><path d="M24 12 L26.4 19.2 L34 19.2 L28 23.6 L30.4 30.8 L24 26.4 L17.6 30.8 L20 23.6 L14 19.2 L21.6 19.2Z" fill="#2c5e2e" opacity="0.85"/><circle cx="24" cy="22" r="3" fill="#e8f4e8" opacity="0.6"/><path d="M24 34 L24 38" stroke="#3d7a40" stroke-width="1.5" stroke-linecap="round"/><path d="M20 36 L24 38 L28 36" stroke="#3d7a40" stroke-width="1" stroke-linecap="round"/>',
    "radical scavenging": '<circle cx="24" cy="22" r="10" fill="#a8cca8" opacity="0.25"/><path d="M24 12 L26.4 19.2 L34 19.2 L28 23.6 L30.4 30.8 L24 26.4 L17.6 30.8 L20 23.6 L14 19.2 L21.6 19.2Z" fill="#2c5e2e" opacity="0.85"/><circle cx="24" cy="22" r="3" fill="#e8f4e8" opacity="0.6"/>',
    "antileishmanial": '<path d="M14 34 C14 34 12 28 16 23 C18 20 21 19 24 19" stroke="#3d7a40" stroke-width="2" stroke-linecap="round" fill="none"/><path d="M34 34 C34 34 36 28 32 23 C30 20 27 19 24 19" stroke="#2c5e2e" stroke-width="2" stroke-linecap="round" fill="none"/><ellipse cx="24" cy="16" rx="6" ry="8" fill="#3d7a40" opacity="0.8"/><ellipse cx="24" cy="13" rx="3.5" ry="5" fill="#5a8a5a" opacity="0.5"/><path d="M24 19 L24 23" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/><ellipse cx="24" cy="35" rx="8" ry="3" fill="#c5dfc5" opacity="0.35"/>',
    "larvicidal":      '<path d="M24 9 C21 9 18 11 17 14 L12 26 C11 29 13 32 16 32 L17 32 L18 38 L30 38 L31 32 L32 32 C35 32 37 29 36 26 L31 14 C30 11 27 9 24 9Z" fill="#3d7a40" opacity="0.75"/><ellipse cx="24" cy="14" rx="4" ry="3" fill="#e8f4e8" opacity="0.3"/><line x1="18" y1="38" x2="18" y2="42" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/><line x1="24" y1="38" x2="24" y2="42" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/><line x1="30" y1="38" x2="30" y2="42" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/>',
    "insecticidal":    '<path d="M24 9 C21 9 18 11 17 14 L12 26 C11 29 13 32 16 32 L17 32 L18 38 L30 38 L31 32 L32 32 C35 32 37 29 36 26 L31 14 C30 11 27 9 24 9Z" fill="#3d7a40" opacity="0.75"/><ellipse cx="24" cy="14" rx="4" ry="3" fill="#e8f4e8" opacity="0.3"/><line x1="18" y1="38" x2="18" y2="42" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/><line x1="24" y1="38" x2="24" y2="42" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/><line x1="30" y1="38" x2="30" y2="42" stroke="#1a3d1e" stroke-width="1.5" stroke-linecap="round"/>',
}

def get_activities(bio_str):
    if not bio_str:
        return []
    seen = set()
    result = []
    for key, (label, icon) in BIOACTIVITY_MAP.items():
        if key in bio_str.lower() and label not in seen:
            seen.add(label)
            result.append((label, icon))
    return result

# ── Image helpers ────────────────────────────────────────────────────────────
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

# ── Search helpers ────────────────────────────────────────────────────────────
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

# ── Admin sidebar ─────────────────────────────────────────────────────────────
ADMIN_PASSWORD = "admin123"

with st.sidebar:
    st.markdown("### 🔐 Admin Panel")
    if st.checkbox("Unlock admin"):
        password = st.text_input("Password", type="password")
        if password == ADMIN_PASSWORD:
            st.success("✅ Logged in")

            st.subheader("🖼️ Plant Images")
            species_list = sorted(species_info.keys())
            selected_species_admin = st.selectbox("Select species", species_list)
            existing_images = get_manual_images(selected_species_admin)
            if existing_images:
                st.write(f"**{len(existing_images)} image(s)**")
                cols = st.columns(min(3, len(existing_images)))
                for idx, img_path in enumerate(existing_images):
                    with cols[idx % 3]:
                        st.image(img_path, use_container_width=True)
                        filename = os.path.basename(img_path)
                        if st.button(f"🗑️ {filename}", key=f"del_{selected_species_admin}_{idx}"):
                            if delete_manual_image(selected_species_admin, filename):
                                st.rerun()
                if st.button("🔥 Delete ALL"):
                    delete_all_images(selected_species_admin)
                    st.rerun()
            else:
                st.info("No images yet.")

            uploaded_files = st.file_uploader("Add image(s)", type=["jpg", "jpeg", "png", "gif"], accept_multiple_files=True)
            if uploaded_files and st.button("💾 Save images"):
                saved = sum(save_manual_image(selected_species_admin, f) for f in uploaded_files)
                if saved:
                    st.success(f"Saved {saved} image(s)")
                    st.rerun()

            st.divider()
            st.subheader("📝 References")
            ref_plant = st.selectbox("Select plant", species_list, key="ref_plant")
            current_pmids = species_info[ref_plant]["pmids"]
            if current_pmids:
                st.write(f"PMIDs: {', '.join(current_pmids)}")
            if ref_plant in manual_refs and manual_refs[ref_plant]:
                st.write("**Current manual refs:**")
                for r in manual_refs[ref_plant]:
                    st.write(f"- {r}")
            manual_refs_input = st.text_area("New references (one per line)", height=120, key="manual_refs_area")
            if st.button("💾 Save refs"):
                ref_list = [l.strip() for l in manual_refs_input.split("\n") if l.strip()]
                manual_refs[ref_plant] = ref_list
                with open(MANUAL_REFS_FILE, "w") as f:
                    json.dump(manual_refs, f, indent=2)
                st.success(f"Saved {len(ref_list)} references")
                st.rerun()
            if ref_plant in manual_refs and manual_refs[ref_plant]:
                if st.button("🗑️ Clear refs"):
                    del manual_refs[ref_plant]
                    with open(MANUAL_REFS_FILE, "w") as f:
                        json.dump(manual_refs, f, indent=2)
                    st.rerun()
        elif password:
            st.error("Wrong password")

# ── HERO ─────────────────────────────────────────────────────────────────────
total_species = len(species_info)
total_compounds = len(df["Compound Name"].unique())
total_activities = len(set(
    k for info in species_info.values()
    for k in BIOACTIVITY_MAP.keys() if k in info["bioactivities"].lower()
))

# ── Hero ─────────────────────────────────────────────────────────────────────
logo_path = "Barakah_roots-removebg-preview.png"
logo_html = ""
if os.path.exists(logo_path):
    with open(logo_path, "rb") as _f:
        _b64 = base64.b64encode(_f.read()).decode()
    # mix-blend-mode:multiply blends the black PNG background into the dark green hero
    logo_html = f'''<img src="data:image/png;base64,{_b64}"
        style="height:190px;width:auto;object-fit:contain;
               mix-blend-mode:multiply;display:block;" />'''

components.html(f"""
<!DOCTYPE html><html><head><style>
  @import url('https://fonts.googleapis.com/css2?family=Lora:wght@600&family=DM+Sans:wght@300;400&display=swap');
  body {{ margin:0; padding:0; background:transparent; }}
  .hero {{
    background: linear-gradient(135deg, #1a3d1e 0%, #2c5e2e 60%, #3d7a40 100%);
    border-radius: 20px;
    padding: 2.5rem 2.5rem;
    display: flex;
    align-items: center;
    gap: 2rem;
    position: relative;
    overflow: hidden;
  }}
  .hero-text {{ flex: 1; }}
  .hero-title {{
    font-family: 'Lora', serif;
    font-size: 2.6rem;
    font-weight: 600;
    color: #e8f4e8;
    margin: 0 0 0.3rem;
    letter-spacing: -0.5px;
  }}
  .hero-sub {{
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: #a8cca8;
    font-weight: 300;
    margin: 0 0 1.2rem;
  }}
  .stats-bar {{
    display: flex;
    gap: 2rem;
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 0.9rem 1.4rem;
    width: fit-content;
  }}
  .stat-num {{ font-family: 'DM Sans', sans-serif; font-size: 1.5rem; font-weight: 600; color: #c8e6c8; }}
  .stat-lab {{ font-family: 'DM Sans', sans-serif; font-size: 0.68rem; color: #90b490; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px; }}
  .logo-wrap {{ flex-shrink: 0; }}
</style></head><body>
<div class="hero">
  <div class="hero-text">
    <div class="hero-title">Barakah Roots</div>
    <p class="hero-sub">Exploring the medicinal plant heritage of Kenya — backed by science</p>
    <div class="stats-bar">
      <div><div class="stat-num">{total_species}</div><div class="stat-lab">Plant Species</div></div>
      <div><div class="stat-num">{total_compounds}</div><div class="stat-lab">Compounds</div></div>
      <div><div class="stat-num">{total_activities}</div><div class="stat-lab">Bioactivities</div></div>
    </div>
  </div>
  <div class="logo-wrap">{logo_html}</div>
</div>
</body></html>
""", height=240)

# ── SEARCH PANEL ──────────────────────────────────────────────────────────────
st.markdown('<div class="search-card">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1], gap="large")

CONDITION_LIST = [
    "anti‑plasmodial", "antimalarial", "antibacterial", "antifungal",
    "cytotoxic", "anti‑inflammatory", "antioxidant", "antileishmanial"
]

with col1:
    st.markdown("**🔍 Search by health condition**")
    selected_condition = st.selectbox("Condition", ["— select —"] + CONDITION_LIST, label_visibility="collapsed")
    if selected_condition == "— select —":
        selected_condition = ""

with col2:
    st.markdown("**🔎 Search by keyword**")
    keyword = st.text_input("Keyword", placeholder="e.g. malaria, Mwarobaini, bark, fever…", label_visibility="collapsed")

st.markdown('</div>', unsafe_allow_html=True)

# ── QUICK FILTERS (illustrated SVG chips) ────────────────────────────────────
st.markdown("**Quick filters:**")

# Build deduplicated list of unique (key, label) pairs
seen_labels = set()
unique_chips = []
for key, (label, _) in BIOACTIVITY_MAP.items():
    if label not in seen_labels:
        seen_labels.add(label)
        unique_chips.append((key, label))

# Render illustrated chip grid
chips_html = '<div class="qf-grid">'
for key, label in unique_chips:
    inner_svg = CHIP_SVGS.get(key, "")
    chips_html += f"""<div class="qf-chip">
      <svg width="44" height="44" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">{inner_svg}</svg>
      <span class="qf-chip-label">{label}</span>
    </div>"""
chips_html += "</div>"
st.markdown(chips_html, unsafe_allow_html=True)

# Store quick_filter in session_state so it persists across reruns
if "quick_filter" not in st.session_state:
    st.session_state["quick_filter"] = None

btn_cols = st.columns(len(unique_chips))
for i, (key, label) in enumerate(unique_chips):
    with btn_cols[i]:
        if st.button(label, key=f"chip_{key}", use_container_width=True):
            st.session_state["quick_filter"] = key

quick_filter = st.session_state["quick_filter"]

# Clear quick_filter if user typed a keyword or chose a dropdown condition
if selected_condition or keyword:
    st.session_state["quick_filter"] = None
    quick_filter = None

# ── RESOLVE RESULTS ───────────────────────────────────────────────────────────
if quick_filter:
    results = search_by_condition(quick_filter)
elif selected_condition:
    results = search_by_condition(selected_condition)
elif keyword:
    results = search_by_keyword(keyword)
else:
    results = []

# ── NO SEARCH YET ────────────────────────────────────────────────────────────
if not results and not selected_condition and not keyword and not quick_filter:
    st.markdown("---")
    st.markdown("##### 🌱 Featured plants")
    featured = list(species_info.keys())[:6]

    selected_featured = st.selectbox(
        "Select a plant to explore →",
        ["— browse —"] + featured,
        format_func=lambda x: f"🌿 {x}" if x != "— browse —" else x,
    )

    feat_cols = st.columns(3)
    for i, sp in enumerate(featured):
        info = species_info[sp]
        activities = get_activities(info["bioactivities"])
        local = get_local_names(sp)
        with feat_cols[i % 3]:
            badges = " ".join([f'<span class="activity-badge">{icon} {label}</span>' for label, icon in activities[:2]])
            st.markdown(f"""
            <div class="result-card">
              <div class="result-card-name">{sp}</div>
              <div class="result-card-meta">{", ".join(local[:2])}</div>
              <div style="margin-top:8px">{badges}</div>
            </div>
            """, unsafe_allow_html=True)

    if selected_featured and selected_featured != "— browse —":
        results = [selected_featured]

# ── RESULTS LIST ──────────────────────────────────────────────────────────────
if results:
    st.markdown(f"### 🌿 {len(results)} plant{'s' if len(results) != 1 else ''} found")

    # Sort alphabetically, show selectbox
    results_sorted = sorted(results)
    selected_plant = st.selectbox(
        "Select a plant to view its full profile →",
        results_sorted,
        format_func=lambda x: f"🌿 {x}"
    )

    # Show result chips
    chip_row = st.columns(min(4, len(results_sorted)))
    for i, sp in enumerate(results_sorted[:8]):
        with chip_row[i % 4]:
            info = species_info[sp]
            acts = get_activities(info["bioactivities"])
            act_str = ", ".join([l for l, _ in acts[:2]]) if acts else "—"
            st.markdown(f"""
            <div class="result-card" style="margin-bottom:0.5rem">
              <div class="result-card-name" style="font-size:0.9rem">{sp}</div>
              <div class="result-card-meta">{act_str}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── PLANT PROFILE ─────────────────────────────────────────────────────────
    if selected_plant:
        info = species_info[selected_plant]
        local_names = get_local_names(selected_plant)
        activities = get_activities(info["bioactivities"])
        preparation = get_preparation(selected_plant)
        manual_images = get_manual_images(selected_plant)
        num_compounds = len(info["compounds"])
        num_refs = len(info["pmids"]) + len(info["links"])

        st.markdown('<div class="profile-card">', unsafe_allow_html=True)

        # ── Top section ──
        col_left, col_right = st.columns([3, 2], gap="large")

        with col_left:
            st.markdown(f'<div class="plant-title">{selected_plant}</div>', unsafe_allow_html=True)

            # Local name badges
            badges_html = " ".join([f'<span class="local-name-badge">🏷️ {n}</span>' for n in local_names])
            st.markdown(badges_html, unsafe_allow_html=True)

            # KPI metrics
            st.markdown(f"""
            <div class="metric-grid" style="margin-top:1.2rem">
              <div class="metric-box">
                <div class="metric-value">{num_compounds}</div>
                <div class="metric-label">Compounds</div>
              </div>
              <div class="metric-box">
                <div class="metric-value">{len(activities)}</div>
                <div class="metric-label">Bioactivities</div>
              </div>
              <div class="metric-box">
                <div class="metric-value">{num_refs}</div>
                <div class="metric-label">References</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with col_right:
            if manual_images:
                st.image(manual_images[0], use_container_width=True)
                if len(manual_images) > 1:
                    thumb_cols = st.columns(min(3, len(manual_images) - 1))
                    for i, img_path in enumerate(manual_images[1:4]):
                        with thumb_cols[i % 3]:
                            st.image(img_path, use_container_width=True)
            else:
                st.markdown("""
                <div style="background:#f0f7f0; border-radius:14px; height:220px; display:flex;
                    flex-direction:column; align-items:center; justify-content:center;
                    border: 2px dashed #c5dfc5; color:#7aaa7a; font-size:0.9rem">
                  <div style="font-size:3rem">🌿</div>
                  <div style="margin-top:0.5rem">No image yet</div>
                  <div style="font-size:0.75rem; color:#aaa; margin-top:4px">Add via admin panel</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # ── Bioactivities ──
        st.markdown('<div class="section-heading">⚗️ Bioactivities</div>', unsafe_allow_html=True)
        if activities:
            acts_html = " ".join([f'<span class="activity-badge">{icon} {label}</span>' for label, icon in activities])
            st.markdown(acts_html, unsafe_allow_html=True)
        else:
            st.info("No specific bioactivities recorded.")

        # ── Preparation ──
        st.markdown('<div class="section-heading">🫙 Traditional Preparation</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#3a4a3a; line-height:1.7">{preparation}</p>', unsafe_allow_html=True)

        # ── Active compounds ──
        st.markdown('<div class="section-heading">🔬 Active Compounds</div>', unsafe_allow_html=True)
        if info["compounds"]:
            show_all = st.session_state.get(f"show_all_{selected_plant}", False)
            display_compounds = info["compounds"] if show_all else info["compounds"][:20]
            chips_html = " ".join([f'<span class="compound-chip">{c}</span>' for c in display_compounds])
            st.markdown(chips_html, unsafe_allow_html=True)
            if len(info["compounds"]) > 20 and not show_all:
                if st.button(f"Show all {len(info['compounds'])} compounds ▾", key=f"show_all_btn_{selected_plant}"):
                    st.session_state[f"show_all_{selected_plant}"] = True
                    st.rerun()
            elif show_all and len(info["compounds"]) > 20:
                if st.button("Show fewer ▴", key=f"show_less_btn_{selected_plant}"):
                    st.session_state[f"show_all_{selected_plant}"] = False
                    st.rerun()
        else:
            st.info("No compounds recorded in the dataset.")

        # ── References ──
        st.markdown('<div class="section-heading">📚 Scientific References</div>', unsafe_allow_html=True)

        if selected_plant in manual_refs and manual_refs[selected_plant]:
            for ref in manual_refs[selected_plant]:
                if ref.startswith(('http://', 'https://')):
                    st.markdown(f'<a class="ref-link" href="{ref}" target="_blank">🔗 {ref[:60]}{"..." if len(ref)>60 else ""}</a>', unsafe_allow_html=True)
                elif ref.startswith("10."):
                    st.markdown(f'<a class="ref-link" href="https://doi.org/{ref}" target="_blank">📄 DOI: {ref}</a>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="ref-link">📝 {ref}</span>', unsafe_allow_html=True)
        else:
            ref_links = []
            for pmid in info["pmids"]:
                if pmid.isdigit():
                    ref_links.append(("pubmed", pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
            for link in info["links"]:
                link = link.strip()
                if link.startswith(('http://', 'https://')):
                    ref_links.append(("link", link[:50], link))
                elif link.startswith("10."):
                    ref_links.append(("doi", link, f"https://doi.org/{link}"))

            seen = set()
            unique_refs = [(t, l, u) for t, l, u in ref_links if u not in seen and not seen.add(u)]

            if unique_refs:
                for ref_type, label, url in unique_refs:
                    icon = "🔬" if ref_type == "pubmed" else ("📄" if ref_type == "doi" else "🔗")
                    prefix = "PubMed" if ref_type == "pubmed" else ("DOI" if ref_type == "doi" else "Link")
                    st.markdown(f'<a class="ref-link" href="{url}" target="_blank">{icon} {prefix}: {label}</a>', unsafe_allow_html=True)
            elif info["references_text"]:
                refs = re.split(r'[;\n]+', info["references_text"])
                for ref in refs[:5]:
                    ref = ref.strip()
                    if ref:
                        st.markdown(f'<span class="ref-link">📝 {ref[:120]}{"..." if len(ref)>120 else ""}</span>', unsafe_allow_html=True)
            else:
                st.info("No references available. Use admin panel to add manual references.")

        st.markdown('</div>', unsafe_allow_html=True)  # close profile-card

        st.markdown("---")
        if st.button("← Back to results"):
            st.session_state["quick_filter"] = None
            st.rerun()

if not results and (selected_condition or keyword or quick_filter):
    st.warning("⚠️ No plants found. Try a different keyword or condition.")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer-bar">
  🌿 Barakah Roots · Kenyan medicinal plant knowledge · Data from peer-reviewed scientific literature<br>
  Add images and references via the admin panel (sidebar)
</div>
""", unsafe_allow_html=True)