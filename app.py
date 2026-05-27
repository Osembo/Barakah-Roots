import streamlit as st
import pandas as pd
import os, shutil, re, json, base64
from PIL import Image
import io

st.set_page_config(
    page_title="Barakah Roots",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Lato:wght@300;400;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    font-family: 'Lato', sans-serif !important;
    background: #f5f1ea !important;
    color: #1a2e1c !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1080px !important; }

/* ── HERO ─────────────────────────────────────────── */
.hero {
    background: #1a3a1e;
    border-radius: 20px;
    display: grid;
    grid-template-columns: 1fr 220px;
    overflow: hidden;
    min-height: 200px;
    margin-bottom: 2.5rem;
}
.hero-left { padding: 2.6rem 3rem; display: flex; flex-direction: column; justify-content: center; gap: 0.35rem; }
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3rem; color: #eaf2ea; line-height: 1;
    letter-spacing: -0.5px; font-weight: 400;
}
.hero-tagline { font-size: 0.75rem; color: #6a9a6a; font-weight: 300; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.8rem; }
.hero-stats { display: flex; gap: 2.5rem; }
.stat-val { font-family: 'DM Serif Display', serif; font-size: 2rem; color: #c8e0c8; line-height: 1; }
.stat-lab { font-size: 0.62rem; color: #4a7a4a; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px; }
.hero-right {
    display: flex; align-items: flex-end; justify-content: center;
    overflow: hidden; padding: 0;
}
.hero-right img {
    width: 220px; height: 220px; object-fit: cover; object-position: center top; display: block;
}
.hero-right-empty {
    font-size: 7rem; padding-bottom: 0.5rem; opacity: 0.6; display: flex; align-items: flex-end;
}

/* ── SEARCH ───────────────────────────────────────── */
div[data-testid="stTextInput"] input {
    background: #ffffff !important;
    border: 1.5px solid #ddd8ce !important;
    border-radius: 50px !important;
    padding: 0.9rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-family: 'Lato', sans-serif !important;
    color: #1a3a1e !important;
    box-shadow: none !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #3d7a40 !important;
    box-shadow: 0 0 0 3px rgba(61,122,64,0.1) !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #bbb !important; }

/* ── FILTER CHIPS ─────────────────────────────────── */
.filter-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: #9aaa9a; margin-bottom: 0.7rem; }
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 0.4rem; }
.chip {
    display: inline-flex; align-items: center; gap: 7px;
    background: #fff; border: 1.5px solid #ddd8ce; border-radius: 50px;
    padding: 6px 14px 6px 10px; cursor: pointer;
    font-size: 0.8rem; font-weight: 500; color: #4a5a4a;
    transition: all 0.15s; user-select: none;
}
.chip:hover { border-color: #3d7a40; background: #f0f7f0; }
.chip.active { background: #1a3a1e; border-color: #1a3a1e; color: #c8e0c8; }
.chip-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* Streamlit buttons (filter chips row only) */
.stButton > button {
    background: transparent !important; border: 1.5px solid #c5dfc5 !important;
    color: #2c5e2e !important; border-radius: 50px !important;
    font-family: 'Lato', sans-serif !important; font-size: 0.82rem !important;
    padding: 0.45rem 1.4rem !important; font-weight: 400 !important;
    transition: all 0.15s !important;
}
.stButton > button:hover { background: #eef6ee !important; border-color: #3d7a40 !important; }
.stButton > button:focus { box-shadow: none !important; }

/* ── RESULTS HEADER ───────────────────────────────── */
.results-header {
    font-family: 'DM Serif Display', serif; font-style: italic;
    font-size: 1.35rem; color: #1a3a1e; margin: 1.2rem 0 0.8rem;
}

/* ── PLANT GRID ───────────────────────────────────── */
.plant-card-wrap {
    position: relative;
    margin-bottom: 10px;
}
.plant-card {
    background: #fff;
    border: 1.5px solid #ddd8ce;
    border-radius: 14px;
    padding: 1rem 1.1rem 1rem;
    pointer-events: none;
    transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}
.plant-card-wrap:hover .plant-card {
    border-color: #3d7a40;
    box-shadow: 0 4px 16px rgba(28,61,32,0.09);
    transform: translateY(-1px);
}
.card-name { font-family: 'DM Serif Display', serif; font-style: italic; font-size: 1rem; color: #1a3a1e; line-height: 1.3; margin-bottom: 3px; font-weight: 400; }
.card-local { font-size: 0.68rem; color: #9aaa9a; margin-bottom: 6px; }
.card-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.tag { font-size: 0.62rem; padding: 2px 8px; border-radius: 20px; background: #eef6ee; color: #2c5e2e; border: 1px solid #d0e8d0; font-weight: 700; }

/* Invisible overlay button */
.plant-card-wrap > div[data-testid="stButton"] {
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    width: 100% !important; height: 100% !important;
    margin: 0 !important;
}
.plant-card-wrap > div[data-testid="stButton"] > button {
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    width: 100% !important; height: 100% !important;
    background: transparent !important;
    border: none !important;
    border-radius: 14px !important;
    color: transparent !important;
    cursor: pointer !important;
    padding: 0 !important;
    font-size: 0 !important;
    box-shadow: none !important;
    outline: none !important;
}
.plant-card-wrap > div[data-testid="stButton"] > button:focus {
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}

/* ── PROFILE ──────────────────────────────────────── */
.back-link {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.82rem; color: #6a7a6a; cursor: pointer;
    text-decoration: none; margin-bottom: 1.8rem;
    background: none; border: none; padding: 0;
    font-family: 'Lato', sans-serif;
}
.back-link:hover { color: #1a3a1e; }
.profile-name {
    font-family: 'DM Serif Display', serif; font-style: italic;
    font-size: 2.6rem; color: #1a3a1e; line-height: 1.1; margin-bottom: 0.25rem; font-weight: 400;
}
.profile-local { font-size: 0.85rem; color: #9aaa9a; margin-bottom: 1.5rem; }
.kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 1.8rem; }
.kpi { background: #ede8df; border-radius: 10px; padding: 0.8rem 1rem; text-align: center; }
.kpi-val { font-family: 'DM Serif Display', serif; font-size: 1.9rem; color: #1a3a1e; line-height: 1; }
.kpi-lab { font-size: 0.6rem; color: #6a7a6a; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }
.section-title {
    font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.12em; color: #9aaa9a;
    padding-bottom: 6px; border-bottom: 1px solid #ddd8ce; margin: 1.8rem 0 0.7rem;
}
.activity-pill {
    display: inline-block; background: #eef6ee; color: #1a3a1e;
    border-radius: 20px; padding: 4px 12px; font-size: 0.78rem; font-weight: 700;
    margin: 2px 3px 2px 0; border: 1px solid #d0e8d0;
}
.compound-tag {
    display: inline-block; background: #f5f1ea; color: #4a5a4a;
    border-radius: 6px; padding: 3px 8px; font-size: 0.73rem; margin: 2px; border: 1px solid #ddd8ce;
}
.ref-pill {
    display: inline-flex; align-items: center; gap: 5px; background: #f5f1ea;
    border: 1px solid #ddd8ce; border-radius: 8px; padding: 5px 10px;
    font-size: 0.75rem; color: #2c5e2e; text-decoration: none; margin: 2px 3px 2px 0;
    font-weight: 700;
}
.ref-pill:hover { background: #e8f4e8; }
.prep-text { font-size: 0.9rem; color: #3a4a3a; line-height: 1.85; }
.img-placeholder {
    background: #ede8df; border-radius: 16px; aspect-ratio: 4/5;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    border: 2px dashed #c5dfc5; color: #9aaa9a; font-size: 0.8rem; gap: 0.5rem; text-align: center;
}
.no-results { text-align: center; padding: 3rem 1rem; color: #9aaa9a; font-size: 0.9rem; font-style: italic; }

/* ── SELECTBOX ────────────────────────────────────── */
div[data-testid="stSelectbox"] > div > div {
    background: #fff !important; border-color: #ddd8ce !important; border-radius: 12px !important;
    font-family: 'Lato', sans-serif !important;
}

/* ── SIDEBAR ──────────────────────────────────────── */
[data-testid="stSidebar"] { background: #1a3a1e !important; }
[data-testid="stSidebar"] * { color: #c8e0c8 !important; }
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea { background: #2c5e2e !important; border-color: #3d7a40 !important; color: #eaf2ea !important; }
[data-testid="stSidebar"] .stButton > button { color: #c8e0c8 !important; border-color: #3d7a40 !important; }

/* ── FOOTER ───────────────────────────────────────── */
.footer {
    text-align: center; padding: 2rem 0 0.5rem; font-size: 0.7rem;
    color: #b0a898; border-top: 1px solid #ddd8ce; margin-top: 3rem;
    letter-spacing: 0.05em;
}

/* Divider */
.divider { border: none; border-top: 1px solid #ddd8ce; margin: 0.5rem 0 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")
    return df.dropna(subset=["Compound Name"])

try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ kenyan_compounds.xlsx not found. Please place it in the same directory.")
    st.stop()

def parse_species(s):
    return [] if pd.isna(s) else [x.strip() for x in str(s).split(";")]

expanded_rows = []
for _, row in df.iterrows():
    for sp in parse_species(row.get("Species", "")):
        expanded_rows.append({
            "species": sp,
            "compound": row["Compound Name"],
            "bioactivities": row["Bioactivities"] if pd.notna(row.get("Bioactivities", "")) else "",
            "pmids": row["PMIDs"] if pd.notna(row.get("PMIDs", "")) else "",
            "links": row["Links"] if pd.notna(row.get("Links", "")) else "",
            "references_text": row["References"] if pd.notna(row.get("References", "")) else "",
        })

species_df = pd.DataFrame(expanded_rows)
species_info = {}
for sp, grp in species_df.groupby("species"):
    pmids = sorted(set(p.strip() for v in grp["pmids"] if pd.notna(v) for p in str(v).split(";") if p.strip()))
    links = sorted(set(l.strip() for v in grp["links"] if pd.notna(v) for l in str(v).split(";") if l.strip()))
    ref_t = next((str(v).strip() for v in grp["references_text"] if pd.notna(v) and str(v).strip()), "")
    species_info[sp] = {
        "compounds": grp["compound"].unique().tolist(),
        "bioactivities": "; ".join(grp["bioactivities"].dropna().unique()),
        "pmids": pmids,
        "links": links,
        "references_text": ref_t,
    }

MANUAL_REFS_FILE    = "manual_references.json"
PLANT_CONTENT_FILE  = "plant_content.json"
manual_refs    = json.load(open(MANUAL_REFS_FILE))   if os.path.exists(MANUAL_REFS_FILE)   else {}
plant_content  = json.load(open(PLANT_CONTENT_FILE)) if os.path.exists(PLANT_CONTENT_FILE) else {}

def save_plant_content():
    json.dump(plant_content, open(PLANT_CONTENT_FILE, "w"), indent=2)

def get_description(sp):
    return plant_content.get(sp, {}).get("description", "")

def get_preparation(sp):
    # Admin-saved value takes priority; fall back to hardcoded dict
    saved = plant_content.get(sp, {}).get("preparation", "")
    if saved:
        return saved
    return preparation_dict.get(sp, "Traditionally, the plant parts are boiled in water or soaked overnight to extract the medicinal compounds.")

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
    "Warburgia ugandensis": "Bark is boiled in water to make a decoction. Leaves can be crushed and applied topically for skin conditions.",
    "Erythrina abyssinica": "Root bark is pounded and mixed with cold water for malaria. Leaves are used as a tea for fever.",
    "Aloe secundiflora": "Leaf sap is extracted and applied directly or mixed with water for internal use and skin care.",
    "Croton megalocarpoides": "Roots are chewed or made into a decoction for stomach ailments.",
    "Terminalia brownii": "Bark is soaked in water overnight and drunk for bacterial infections.",
    "Millettia dura": "Seeds are crushed and used as a fish poison; bark decoction used for fever.",
    "Vepris uguenensis": "Leaves are steamed and inhaled for respiratory problems; roots used for malaria.",
    "Zanthoxylum usambarense": "Roots and bark are chewed or boiled for toothache, malaria, and bacterial infections.",
}

ACTIVITIES = [
    ("antimalarial",        "Antimalarial",       "anti\u2011plasmodial", "#3d7a40"),
    ("antibacterial",       "Antibacterial",       "antimicrobial",        "#1a7a6a"),
    ("antifungal",          "Antifungal",          None,                   "#5a4ab0"),
    ("cytotoxic",           "Anticancer",          "anticancer",           "#a03030"),
    ("anti\u2011inflammatory","Anti-inflammatory", None,                   "#2060a0"),
    ("antioxidant",         "Antioxidant",         "radical scavenging",   "#a08010"),
    ("antileishmanial",     "Antileishmanial",     None,                   "#803080"),
    ("larvicidal",          "Insecticidal",        "insecticidal",         "#607020"),
]

def get_local_names(sp):
    return local_names_dict.get(sp, [f"Wild {sp.split()[0]}"])


def get_activity_labels(bio_str):
    if not bio_str: return []
    bio = bio_str.lower(); seen = set(); result = []
    for key, label, alt, _ in ACTIVITIES:
        if key in bio or (alt and alt in bio):
            if label not in seen:
                seen.add(label); result.append(label)
    return result

def search_keyword(q):
    q = q.lower().strip()
    if not q: return []
    out = []
    for sp, info in species_info.items():
        names = [sp.lower()] + [n.lower() for n in get_local_names(sp)]
        if (q in sp.lower() or any(q in n for n in names)
                or q in info["bioactivities"].lower()
                or any(q in c.lower() for c in info["compounds"])):
            out.append(sp)
    return sorted(out)

def search_activity(label):
    key, _, alt, _ = next((a for a in ACTIVITIES if a[1] == label), (None, None, None, None))
    if not key: return []
    return sorted([sp for sp, i in species_info.items()
                   if key in i["bioactivities"].lower() or (alt and alt in i["bioactivities"].lower())])

# ── Image helpers ─────────────────────────────────────────────────────────────
os.makedirs("plant_images", exist_ok=True)

def get_img_dir(sp):
    d = os.path.join("plant_images", sp.replace("/", "_").replace("\\", "_"))
    os.makedirs(d, exist_ok=True)
    return d

def get_images(sp):
    d = get_img_dir(sp)
    return sorted([os.path.join(d, f) for f in os.listdir(d)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])

def save_image(sp, uploaded):
    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif']: return False
    n = len(get_images(sp)) + 1
    with open(os.path.join(get_img_dir(sp), f"image_{n}{ext}"), "wb") as f:
        f.write(uploaded.getbuffer())
    return True

def get_logo_b64():
    p = "Barakah_roots-removebg-preview.png"
    if not os.path.exists(p): return None
    try:
        img = Image.open(p).convert("RGBA")
        data = img.getdata()
        img.putdata([(0, 0, 0, 0) if r < 45 and g < 45 and b < 45 else (r, g, b, a)
                     for r, g, b, a in data])
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return base64.b64encode(open(p, "rb").read()).decode()

# ── Plant grid renderer ───────────────────────────────────────────────────────
def render_plant_grid(plants):
    COLS = 4
    for row_start in range(0, len(plants), COLS):
        row = plants[row_start:row_start + COLS]
        cols = st.columns(COLS)
        for col, sp in zip(cols, row):
            info = species_info[sp]
            local = get_local_names(sp)
            acts  = get_activity_labels(info["bioactivities"])
            tags_html = "".join(f'<span class="tag">{a}</span>' for a in acts[:3])
            with col:
                # Wrapper div that handles hover via CSS
                st.markdown(f"""
                <div class="plant-card-wrap">
                  <div class="plant-card">
                    <div class="card-name">{sp}</div>
                    <div class="card-local">{" · ".join(local[:2])}</div>
                    <div class="card-tags">{tags_html}</div>
                  </div>
                """, unsafe_allow_html=True)
                # Invisible full-size button overlaid on top
                if st.button("open", key=f"card_{sp}", use_container_width=True):
                    st.session_state.selected_plant = sp
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

# ── Admin sidebar ─────────────────────────────────────────────────────────────
ADMIN_PASSWORD = "admin123"
with st.sidebar:
    st.markdown("### 🌿 Admin")
    if st.checkbox("🔐 Unlock admin"):
        pw = st.text_input("Password", type="password")
        if pw == ADMIN_PASSWORD:
            st.success("Logged in")
            sp_list = sorted(species_info.keys())

            # ── Images ────────────────────────────────────────
            st.subheader("Images")
            sp_admin = st.selectbox("Species", sp_list, key="img_sp")
            imgs = get_images(sp_admin)
            if imgs:
                cols = st.columns(min(3, len(imgs)))
                for i, p in enumerate(imgs):
                    with cols[i % 3]:
                        st.image(p, use_container_width=True)
                        if st.button("🗑️", key=f"del_{i}"): os.remove(p); st.rerun()
                if st.button("Delete all images"):
                    shutil.rmtree(get_img_dir(sp_admin)); st.rerun()
            up = st.file_uploader("Upload images", type=["jpg", "jpeg", "png", "gif"], accept_multiple_files=True)
            if up and st.button("Save images"):
                st.success(f"Saved {sum(save_image(sp_admin, u) for u in up)}"); st.rerun()

            st.divider()

            # ── Description & Preparation ──────────────────────
            st.subheader("Description & Preparation")
            sp_content = st.selectbox("Species", sp_list, key="content_sp")

            current_desc = plant_content.get(sp_content, {}).get("description", "")
            current_prep = plant_content.get(sp_content, {}).get("preparation",
                preparation_dict.get(sp_content, ""))

            new_desc = st.text_area(
                "Plant description",
                value=current_desc,
                height=130,
                placeholder="Write a general description of this plant — its appearance, habitat, cultural significance…",
                key=f"desc_{sp_content}",
            )
            new_prep = st.text_area(
                "Mode of preparation",
                value=current_prep,
                height=110,
                placeholder="How is this plant traditionally prepared? Decoction, topical, etc.",
                key=f"prep_{sp_content}",
            )
            if st.button("Save description & preparation"):
                if sp_content not in plant_content:
                    plant_content[sp_content] = {}
                plant_content[sp_content]["description"]  = new_desc.strip()
                plant_content[sp_content]["preparation"]  = new_prep.strip()
                save_plant_content()
                st.success("Saved ✓"); st.rerun()

            st.divider()

            # ── References ────────────────────────────────────
            st.subheader("References")
            ref_sp = st.selectbox("Species", sp_list, key="ref_sp")
            if species_info[ref_sp]["pmids"]:
                st.caption(f"PMIDs: {', '.join(species_info[ref_sp]['pmids'])}")
            if ref_sp in manual_refs:
                for r in manual_refs[ref_sp]: st.caption(f"• {r}")
            new_refs = st.text_area("New references (one per line)", height=100)
            if st.button("Save references"):
                manual_refs[ref_sp] = [l.strip() for l in new_refs.split("\n") if l.strip()]
                json.dump(manual_refs, open(MANUAL_REFS_FILE, "w"), indent=2)
                st.success("Saved ✓"); st.rerun()
        elif pw:
            st.error("Wrong password")

# ── Session state ─────────────────────────────────────────────────────────────
if "active_filter" not in st.session_state: st.session_state.active_filter = None
if "selected_plant" not in st.session_state: st.session_state.selected_plant = None

# ── Stats ─────────────────────────────────────────────────────────────────────
total_species   = len(species_info)
total_compounds = len(df["Compound Name"].unique())
total_refs      = sum(len(v["pmids"]) + len(v["links"]) for v in species_info.values())

# ── Hero ──────────────────────────────────────────────────────────────────────
_logo = get_logo_b64()
if _logo:
    hero_right = f'<div class="hero-right"><img src="data:image/png;base64,{_logo}" /></div>'
else:
    hero_right = '<div class="hero-right"><div class="hero-right-empty">🌿</div></div>'

st.markdown(f"""
<div class="hero">
  <div class="hero-left">
    <div class="hero-title">Barakah Roots</div>
    <div class="hero-tagline">Medicinal plant heritage of Kenya · Backed by science</div>
    <div class="hero-stats">
      <div><div class="stat-val">{total_species}</div><div class="stat-lab">Species</div></div>
      <div><div class="stat-val">{total_compounds}</div><div class="stat-lab">Compounds</div></div>
      <div><div class="stat-val">{total_refs}</div><div class="stat-lab">References</div></div>
    </div>
  </div>
  {hero_right}
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PLANT PROFILE VIEW
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.selected_plant:
    sp   = st.session_state.selected_plant
    info = species_info.get(sp, {})
    local = get_local_names(sp)
    acts  = get_activity_labels(info.get("bioactivities", ""))
    imgs  = get_images(sp)
    compounds = info.get("compounds", [])
    num_refs  = len(info.get("pmids", [])) + len(info.get("links", []))

    if st.button("← Back to results"):
        st.session_state.selected_plant = None
        st.rerun()

    col_a, col_b = st.columns([3, 2], gap="large")

    with col_a:
        st.markdown(f'<div class="profile-name">{sp}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profile-local">{" · ".join(local)}</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi"><div class="kpi-val">{len(compounds)}</div><div class="kpi-lab">Compounds</div></div>
          <div class="kpi"><div class="kpi-val">{len(acts)}</div><div class="kpi-lab">Activities</div></div>
          <div class="kpi"><div class="kpi-val">{num_refs}</div><div class="kpi-lab">References</div></div>
        </div>""", unsafe_allow_html=True)

        # Description
        description = get_description(sp)
        st.markdown('<div class="section-title">About this plant</div>', unsafe_allow_html=True)
        if description:
            st.markdown(f'<p class="prep-text">{description}</p>', unsafe_allow_html=True)
        else:
            st.caption("No description yet. Add one via the admin panel.")

        # Preparation
        prep = get_preparation(sp)
        st.markdown('<div class="section-title">Mode of preparation</div>', unsafe_allow_html=True)
        if prep:
            st.markdown(f'<p class="prep-text">{prep}</p>', unsafe_allow_html=True)
        else:
            st.caption("No preparation method recorded. Add one via the admin panel.")

        # Bioactivities
        st.markdown('<div class="section-title">Bioactivities</div>', unsafe_allow_html=True)
        if acts:
            st.markdown(" ".join(f'<span class="activity-pill">{a}</span>' for a in acts), unsafe_allow_html=True)
        else:
            st.caption("None recorded.")

        # Compounds
        st.markdown('<div class="section-title">Active compounds</div>', unsafe_allow_html=True)
        if compounds:
            show_all = st.session_state.get(f"show_all_{sp}", False)
            shown = compounds if show_all else compounds[:24]
            st.markdown(" ".join(f'<span class="compound-tag">{c}</span>' for c in shown), unsafe_allow_html=True)
            if len(compounds) > 24:
                label = "Show fewer" if show_all else f"Show all {len(compounds)}"
                if st.button(label, key=f"toggle_compounds_{sp}"):
                    st.session_state[f"show_all_{sp}"] = not show_all
                    st.rerun()
        else:
            st.caption("None recorded.")

        # References
        st.markdown('<div class="section-title">Scientific references</div>', unsafe_allow_html=True)
        ref_items = list(manual_refs.get(sp, []))
        if not ref_items:
            for pmid in info.get("pmids", []):
                if pmid.isdigit():
                    ref_items.append(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            for link in info.get("links", []):
                link = link.strip()
                if link.startswith("http"): ref_items.append(link)
                elif link.startswith("10."): ref_items.append(f"https://doi.org/{link}")

        seen_r = set()
        ref_html = ""
        for r in ref_items:
            if r in seen_r: continue
            seen_r.add(r)
            if r.startswith("http"):
                lbl = "PubMed" if "pubmed" in r else ("DOI" if "doi.org" in r else "Link")
                short = r[8:55] + ("…" if len(r) > 63 else "")
                ref_html += f'<a class="ref-pill" href="{r}" target="_blank">↗ {lbl}: {short}</a>'
            else:
                ref_html += f'<span class="ref-pill">📄 {r[:90]}</span>'

        if ref_html:
            st.markdown(ref_html, unsafe_allow_html=True)
        else:
            if info.get("references_text"):
                for ref in re.split(r"[;\n]+", info["references_text"])[:5]:
                    ref = ref.strip()
                    if ref:
                        st.markdown(f'<span class="ref-pill">📄 {ref[:100]}</span>', unsafe_allow_html=True)
            else:
                st.caption("No references recorded. Add via admin panel.")


    with col_b:
        if imgs:
            st.image(imgs[0], use_container_width=True)
            if len(imgs) > 1:
                tc = st.columns(min(3, len(imgs) - 1))
                for i, p in enumerate(imgs[1:4]):
                    with tc[i % 3]:
                        st.image(p, use_container_width=True)
        else:
            st.markdown("""
            <div class="img-placeholder">
              <div style="font-size:3.5rem;opacity:0.4">🌿</div>
              <div style="font-weight:700;color:#7a9a7a">No image yet</div>
              <div style="font-size:0.7rem;color:#b0c8b0;margin-top:2px">Upload via admin panel</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="footer">Barakah Roots · Kenyan medicinal plant heritage · Peer-reviewed data</div>', unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# HOME VIEW — Search, Filters, Results
# ═══════════════════════════════════════════════════════════════════════════════

keyword = st.text_input(
    "search",
    placeholder="Search by plant name, condition, compound, or local name…",
    label_visibility="collapsed"
)

if keyword and st.session_state.active_filter:
    st.session_state.active_filter = None

# ── Chip filters ──────────────────────────────────────────────────────────────
chip_html = '<div class="filter-label">Browse by condition</div><div class="chip-row">'
for _, label, _, color in ACTIVITIES:
    active_cls = "active" if st.session_state.active_filter == label else ""
    dot_color = "#7aaa7a" if active_cls else color
    chip_html += (
        f'<div class="chip {active_cls}">'
        f'<span class="chip-dot" style="background:{dot_color}"></span>'
        f'{label}</div>'
    )
chip_html += "</div>"
st.markdown(chip_html, unsafe_allow_html=True)

# Functional buttons (invisible, same row)
btn_cols = st.columns(len(ACTIVITIES))
for i, (_, label, _, _) in enumerate(ACTIVITIES):
    with btn_cols[i]:
        if st.button(label, key=f"f_{label}", use_container_width=True):
            st.session_state.active_filter = None if st.session_state.active_filter == label else label
            st.rerun()

# ── Compute results ───────────────────────────────────────────────────────────
if keyword:
    results = search_keyword(keyword)
elif st.session_state.active_filter:
    results = search_activity(st.session_state.active_filter)
else:
    results = []

# ── Render results ────────────────────────────────────────────────────────────
if results:
    src = f'"{keyword}"' if keyword else f'"{st.session_state.active_filter}"'
    plural = "s" if len(results) != 1 else ""
    st.markdown(
        f'<div class="results-header">{len(results)} plant{plural} matching {src}</div>',
        unsafe_allow_html=True
    )
    render_plant_grid(results)

elif keyword or st.session_state.active_filter:
    st.markdown('<div class="no-results">No plants found. Try a different search.</div>', unsafe_allow_html=True)

else:
    featured = list(species_info.keys())[:8]
    st.markdown('<div class="results-header">Featured plants</div>', unsafe_allow_html=True)
    render_plant_grid(featured)

st.markdown(
    '<div class="footer">Barakah Roots · Kenyan medicinal plant heritage · Peer-reviewed data</div>',
    unsafe_allow_html=True
)