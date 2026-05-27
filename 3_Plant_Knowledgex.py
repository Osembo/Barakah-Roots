"""
pages/3_Plant_Knowledge.py — Species Knowledge Base
=====================================================
The original Barakah Roots plant explorer, integrated as a
read-only knowledge module within the nursery system.
All roles can access this.
"""

import streamlit as st
import pandas as pd
import os, sys, re, json
from PIL import Image
import io, base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from components.auth import require_login, current_user, ROLE_LABELS

require_login()
user = current_user()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,600&family=Inter:wght@300;400;500&display=swap');
html,body,[class*="css"],.stApp { font-family:'Inter',sans-serif; background:#f7f4ee !important; }
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding:2rem 3rem !important; max-width:1100px !important; }
.page-title { font-family:'Cormorant Garamond',serif; font-size:2.2rem; font-weight:600; color:#1c3d20; font-style:italic; margin-bottom:0.2rem; }
.page-sub { font-size:0.8rem; color:#9a9080; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:2rem; }
.profile-name { font-family:'Cormorant Garamond',serif; font-size:2.4rem; font-style:italic; font-weight:600; color:#1c3d20; line-height:1.1; margin-bottom:0.2rem; }
.section-title { font-size:0.63rem; text-transform:uppercase; letter-spacing:0.12em; color:#9a9080; margin:1.8rem 0 0.6rem; padding-bottom:0.4rem; border-bottom:1px solid #e8e2d8; }
.activity-pill { display:inline-block; background:#eef6ee; color:#1c3d20; border-radius:20px; padding:4px 14px; font-size:0.78rem; font-weight:500; margin:3px; border:1px solid #d0e8d0; }
.compound-tag { display:inline-block; background:#f7f4ee; color:#4a5a4a; border-radius:6px; padding:3px 10px; font-size:0.75rem; margin:2px; border:1px solid #e0dbd0; }
.plant-card { background:#fff; border:1.5px solid #e0dbd0; border-radius:14px; padding:1rem 1.2rem; margin-bottom:8px; }
.plant-card-name { font-family:'Cormorant Garamond',serif; font-size:1rem; font-style:italic; color:#1c3d20; font-weight:600; }
.tag { font-size:0.63rem; padding:2px 8px; border-radius:20px; background:#eef6ee; color:#2c5e2e; border:1px solid #d0e8d0; font-weight:500; display:inline-block; margin:2px; }
div[data-testid="stTextInput"] input { background:#fff !important; border:1.5px solid #ddd8ce !important; border-radius:50px !important; padding:0.85rem 1.5rem !important; font-size:1rem !important; }
div[data-testid="stSelectbox"] > div > div { background:#fff !important; border-color:#e0dbd0 !important; border-radius:12px !important; }
.stButton > button { background:transparent !important; border:1.5px solid #c5dfc5 !important; color:#2c5e2e !important; border-radius:50px !important; font-size:0.85rem !important; padding:0.5rem 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Species Knowledge Base</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Kenyan medicinal plants · Peer-reviewed compound data</div>', unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_species_data():
    df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")
    df = df.dropna(subset=["Compound Name"])
    rows = []
    for _, row in df.iterrows():
        sp_raw = row.get("Species", "")
        for sp in ([x.strip() for x in str(sp_raw).split(";")] if pd.notna(sp_raw) else []):
            rows.append({
                "species": sp,
                "compound": row["Compound Name"],
                "bioactivities": row.get("Bioactivities","") if pd.notna(row.get("Bioactivities","")) else "",
                "pmids": row.get("PMIDs","") if pd.notna(row.get("PMIDs","")) else "",
                "links": row.get("Links","") if pd.notna(row.get("Links","")) else "",
            })
    sdf = pd.DataFrame(rows)
    info = {}
    for sp, grp in sdf.groupby("species"):
        pmids = sorted(set(p.strip() for v in grp["pmids"] if pd.notna(v) for p in str(v).split(";") if p.strip()))
        links = sorted(set(l.strip() for v in grp["links"] if pd.notna(v) for l in str(v).split(";") if l.strip()))
        info[sp] = {
            "compounds": grp["compound"].unique().tolist(),
            "bioactivities": "; ".join(grp["bioactivities"].dropna().unique()),
            "pmids": pmids, "links": links,
        }
    return info

try:
    species_info = load_species_data()
except FileNotFoundError:
    st.error("kenyan_compounds.xlsx not found.")
    st.stop()

ACTIVITIES = [
    ("antimalarial","Antimalarial","anti\u2011plasmodial"),
    ("antibacterial","Antibacterial","antimicrobial"),
    ("antifungal","Antifungal",None),
    ("cytotoxic","Anticancer","anticancer"),
    ("anti\u2011inflammatory","Anti-inflammatory",None),
    ("antioxidant","Antioxidant","radical scavenging"),
    ("antileishmanial","Antileishmanial",None),
    ("larvicidal","Insecticidal","insecticidal"),
]

def get_acts(bio):
    if not bio: return []
    b = bio.lower(); seen = set(); out = []
    for key, label, alt in ACTIVITIES:
        if key in b or (alt and alt in b):
            if label not in seen: seen.add(label); out.append(label)
    return out

def do_search(q):
    q = q.lower()
    return sorted([sp for sp, info in species_info.items()
                   if q in sp.lower() or q in info["bioactivities"].lower()
                   or any(q in c.lower() for c in info["compounds"])])

# ── Session state ─────────────────────────────────────────────────────────────
if "kb_plant" not in st.session_state: st.session_state.kb_plant = None

if st.session_state.kb_plant:
    sp   = st.session_state.kb_plant
    info = species_info.get(sp, {})
    acts = get_acts(info.get("bioactivities",""))
    compounds = info.get("compounds",[])

    if st.button("← Back to search"):
        st.session_state.kb_plant = None; st.rerun()

    st.markdown(f'<div class="profile-name">{sp}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3,1])
    with c1:
        st.markdown('<div class="section-title">Bioactivities</div>', unsafe_allow_html=True)
        st.markdown(" ".join(f'<span class="activity-pill">{a}</span>' for a in acts) if acts else "<i style='color:#aaa'>None recorded</i>", unsafe_allow_html=True)

        st.markdown('<div class="section-title">Active Compounds</div>', unsafe_allow_html=True)
        shown = compounds[:30]
        st.markdown(" ".join(f'<span class="compound-tag">{c}</span>' for c in shown), unsafe_allow_html=True)
        if len(compounds) > 30: st.caption(f"…and {len(compounds)-30} more")

        st.markdown('<div class="section-title">References</div>', unsafe_allow_html=True)
        for pmid in info.get("pmids",[])[:5]:
            if pmid.isdigit():
                st.markdown(f'<a style="font-size:0.8rem;color:#2c5e2e" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" target="_blank">↗ PubMed {pmid}</a><br>', unsafe_allow_html=True)
    with c2:
        imgs_dir = os.path.join("plant_images", sp.replace("/","_").replace("\\","_"))
        imgs = sorted([os.path.join(imgs_dir,f) for f in os.listdir(imgs_dir) if f.lower().endswith(('.jpg','.png','.jpeg'))]) if os.path.exists(imgs_dir) else []
        if imgs:
            st.image(imgs[0], use_container_width=True)
        else:
            st.markdown('<div style="background:#f0f7f0;border-radius:12px;height:180px;display:flex;align-items:center;justify-content:center;border:2px dashed #c5dfc5;color:#9abc9a;font-size:2rem">🌿</div>', unsafe_allow_html=True)

else:
    keyword = st.text_input("search", placeholder="Search species, compound, or condition…", label_visibility="collapsed")
    results = do_search(keyword) if keyword else list(species_info.keys())[:12]

    if keyword: st.markdown(f'<div style="font-family:Cormorant Garamond,serif;font-style:italic;color:#1c3d20;font-size:1.2rem;margin:1rem 0">{len(results)} species found</div>', unsafe_allow_html=True)

    grid_html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-bottom:1.5rem">'
    for sp in results:
        acts = get_acts(species_info[sp]["bioactivities"])
        tags = " ".join(f'<span class="tag">{a}</span>' for a in acts[:3])
        grid_html += f'<div class="plant-card"><div class="plant-card-name">{sp}</div><div style="margin-top:6px">{tags}</div></div>'
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

    chosen = st.selectbox("Open profile", ["— select —"] + results, label_visibility="collapsed")
    if chosen and chosen != "— select —":
        st.session_state.kb_plant = chosen; st.rerun()
