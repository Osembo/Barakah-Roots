"""
Home.py — Barakah Roots: Nursery Management System
===================================================
Entry point. Run with: streamlit run Home.py

Module structure:
  Home.py              ← this file
  pages/
    1_Mother_Plants.py ← Mother Plant Registry + Map
    2_Batches.py       ← Batch Management + Task Logger
  data/
    db.py              ← Data layer (all models + persistence)
  components/
    auth.py            ← Role-based access control
    gps.py             ← Offline-first GPS capture

Required packages:
  streamlit pandas openpyxl pillow folium streamlit-folium
  streamlit-geolocation (optional, for device GPS)

Install: pip install streamlit pandas openpyxl pillow folium streamlit-folium
"""

import streamlit as st
import pandas as pd
import os, sys, base64, json
from datetime import datetime
from PIL import Image
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from components.auth import require_login, can, current_user, logout, ROLE_LABELS
from data.db import (
    get_mother_plants, get_batches, get_task_log,
    get_pending_queue, GROWTH_PHASES,
)

st.set_page_config(
    page_title="Barakah Roots — Nursery",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400;1,600&family=Inter:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; background: #f7f4ee !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem !important; max-width: 1200px !important; }

.hero-wrap { background: #1c3d20; border-radius: 24px; overflow: hidden; margin-bottom: 2rem; display: flex; min-height: 180px; }
.hero-left { flex: 1; padding: 2.2rem 3rem; display: flex; flex-direction: column; justify-content: center; }
.hero-logo-col { width: 180px; flex-shrink: 0; overflow: hidden; padding: 0; display: flex; align-items: flex-end; }
.hero-logo-col img { width: 180px; height: 180px; object-fit: cover; object-position: center top; display: block; }
.hero-title { font-family: 'Cormorant Garamond', serif; font-size: 2.6rem; font-weight: 600; color: #e8f0e8; line-height: 1; margin: 0 0 0.25rem; letter-spacing: -0.5px; }
.hero-sub { font-size: 0.78rem; color: #7aaa7a; font-weight: 300; margin: 0 0 1.5rem; letter-spacing: 0.08em; text-transform: uppercase; }
.hero-stats { display: flex; gap: 2rem; }
.stat-num { font-family: 'Cormorant Garamond', serif; font-size: 1.8rem; font-weight: 600; color: #c8e0c8; line-height: 1; }
.stat-lab { font-size: 0.6rem; color: #5a885a; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 2px; }

.dash-card { background: #fff; border: 1.5px solid #e0dbd0; border-radius: 16px; padding: 1.4rem 1.6rem; height: 100%; }
.dash-card-title { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: #9a9080; margin-bottom: 1rem; border-bottom: 1px solid #e8e2d8; padding-bottom: 0.5rem; }
.phase-row { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f0ece4; font-size: 0.82rem; }
.phase-row:last-child { border-bottom: none; }
.phase-count { font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; font-weight: 600; color: #1c3d20; }
.activity-row { padding: 6px 0; border-bottom: 1px solid #f0ece4; font-size: 0.8rem; }
.activity-row:last-child { border-bottom: none; }

[data-testid="stSidebar"] { background: #1c3d20 !important; }
[data-testid="stSidebar"] * { color: #c8e0c8 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #e8f0e8 !important; border-radius: 8px !important;
    font-size: 0.82rem !important; width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
require_login()
user = current_user()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    logo_path = "Barakah_roots-removebg-preview.png"
    if os.path.exists(logo_path):
        try:
            img = Image.open(logo_path).convert("RGBA")
            data = img.getdata()
            img.putdata([(0,0,0,0) if r<45 and g<45 and b<45 else (r,g,b,a) for r,g,b,a in data])
            buf = io.BytesIO(); img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            st.markdown(f'<div style="text-align:center;padding:1rem 0"><img src="data:image/png;base64,{b64}" style="height:90px;object-fit:contain"></div>', unsafe_allow_html=True)
        except Exception:
            pass

    st.markdown(f"""
    <div style="text-align:center;padding-bottom:1rem;border-bottom:1px solid rgba(255,255,255,0.1)">
      <div style="font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-style:italic;color:#e8f0e8">Barakah Roots</div>
      <div style="font-size:0.65rem;color:#7aaa7a;letter-spacing:0.1em;text-transform:uppercase">Nursery Management</div>
    </div>
    <div style="padding:1rem 0 0.5rem;font-size:0.72rem;color:#7aaa7a">
      Signed in as <b style="color:#c8e0c8">{user['display_name']}</b><br>
      {ROLE_LABELS.get(user['role'],'—')}
    </div>
    """, unsafe_allow_html=True)

    # Offline queue warning
    pending = get_pending_queue()
    if pending:
        st.warning(f"📡 {len(pending)} GPS log(s) pending sync")

    st.markdown("---")
    st.page_link("Home.py",                  label="🏠 Dashboard")
    st.page_link("pages/1_Mother_Plants.py", label="🌳 Mother Plants")
    st.page_link("pages/2_Batches.py",       label="🌱 Batches & Tasks")

    st.markdown("---")
    st.markdown('<div style="font-size:0.65rem;color:#5a885a;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Plant Knowledge Base</div>', unsafe_allow_html=True)
    st.page_link("pages/3_Plant_Knowledge.py", label="📖 Species Explorer")

    st.markdown("---")
    if st.button("Sign out"):
        logout(); st.rerun()

# ── Hero ──────────────────────────────────────────────────────────────────────
mothers  = get_mother_plants()
batches  = get_batches()
tasks    = get_task_log()
active_b = [b for b in batches if b.get("is_active")]

logo_tag = ""
if os.path.exists(logo_path):
    try:
        img = Image.open(logo_path).convert("RGBA")
        d = img.getdata(); img.putdata([(0,0,0,0) if r<45 and g<45 and b<45 else (r,g,b,a) for r,g,b,a in d])
        buf = io.BytesIO(); img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        logo_tag = f'<img src="data:image/png;base64,{b64}" style="width:180px;height:180px;object-fit:cover;object-position:center top;display:block;">'
    except Exception: pass

st.markdown(f"""
<div class="hero-wrap">
  <div class="hero-left">
    <div class="hero-title">Nursery Dashboard</div>
    <div class="hero-sub">Barakah Roots · Provenance Tracking System</div>
    <div class="hero-stats">
      <div><div class="stat-num">{len(mothers)}</div><div class="stat-lab">Mother Plants</div></div>
      <div><div class="stat-num">{len(active_b)}</div><div class="stat-lab">Active Batches</div></div>
      <div><div class="stat-num">{sum(b.get('cutting_count',0) for b in active_b)}</div><div class="stat-lab">Cuttings</div></div>
      <div><div class="stat-num">{len(tasks)}</div><div class="stat-lab">Tasks Logged</div></div>
    </div>
  </div>
  <div class="hero-logo-col">{logo_tag}</div>
</div>
""", unsafe_allow_html=True)

# ── Dashboard cards ───────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1.2, 1.2, 1], gap="medium")

# Card 1: Growth Phase Breakdown
with col1:
    phase_counts = {p: len([b for b in active_b if b["growth_phase"] == p]) for p in GROWTH_PHASES}
    phase_icons  = {"Germination": "🌰", "Rapid Growth": "🌿", "Hardening": "🌱", "Ready for Field": "✅"}
    rows = "".join(
        f'<div class="phase-row"><span>{phase_icons.get(p,"")}&nbsp;{p}</span><span class="phase-count">{phase_counts[p]}</span></div>'
        for p in GROWTH_PHASES
    )
    st.markdown(f'<div class="dash-card"><div class="dash-card-title">Growth Phase Breakdown</div>{rows}</div>', unsafe_allow_html=True)

# Card 2: Recent Activity
with col2:
    recent_tasks = tasks[:8]
    if recent_tasks:
        rows = "".join(
            f'<div class="activity-row"><span style="font-weight:500;color:#1c3d20">{t["task_type"]}</span>'
            f'&nbsp;<span style="color:#9a9080;font-size:0.72rem">· {t["batch_id"]}</span><br>'
            f'<span style="color:#7a8a7a;font-size:0.75rem">{t["logged_by"]} · {t["logged_at"][5:16].replace("T"," ")}</span></div>'
            for t in recent_tasks
        )
    else:
        rows = '<div style="color:#9a9080;font-size:0.82rem;padding:1rem 0">No activity yet.</div>'
    st.markdown(f'<div class="dash-card"><div class="dash-card-title">Recent Activity</div>{rows}</div>', unsafe_allow_html=True)

# Card 3: Quick Actions
with col3:
    st.markdown('<div class="dash-card"><div class="dash-card-title">Quick Actions</div>', unsafe_allow_html=True)
    if can("create_mother_plant"):
        st.page_link("pages/1_Mother_Plants.py", label="➕ Register Mother Plant")
    if can("create_batch"):
        st.page_link("pages/2_Batches.py",       label="🌱 Create New Batch")
    st.page_link("pages/2_Batches.py",           label="📝 Log a Task")
    st.page_link("pages/1_Mother_Plants.py",     label="🗺️ View Plant Map")
    st.markdown('</div>', unsafe_allow_html=True)

    if pending:
        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
        st.warning(f"📡 **{len(pending)} offline GPS log(s)** awaiting sync. Go to Mother Plants → GPS to sync.")

# ── Schema overview (admin only) ─────────────────────────────────────────────
if can("admin"):
    with st.expander("🗄️ Database Schema Overview (Admin)", expanded=False):
        st.code("""
SCHEMA: Barakah Roots Nursery Management
==========================================

species_info  (existing, from Excel)
  └─ species: str  ←──────── mother_plants.species (FK by name)

mother_plants
  ├─ id:              str  PRIMARY KEY  (e.g. MP-A3F2)
  ├─ species:         str  FK → species_info
  ├─ phenotype_id:    str
  ├─ phenotype_tags:  list
  ├─ location_name:   str
  ├─ gps_lat:         float
  ├─ gps_lng:         float
  ├─ gps_accuracy_m:  float
  ├─ gps_method:      str
  ├─ notes:           str
  ├─ image_path:      str
  ├─ registered_by:   str
  └─ registered_at:   datetime

batches  [ONE-TO-MANY from mother_plants]
  ├─ id:               str  PRIMARY KEY  (e.g. BAT-9C1A)
  ├─ mother_plant_id:  str  FK → mother_plants.id  ★ provenance link
  ├─ species:          str  (denormalised for query speed)
  ├─ phenotype_id:     str  (inherited)
  ├─ nursery_location: str
  ├─ planting_date:    date
  ├─ cutting_count:    int
  ├─ growth_phase:     str  ENUM(GROWTH_PHASES)
  ├─ compliance_log:   list[str]
  ├─ passport_qr_code: null  ← RESERVED for QR Passport feature
  └─ lab_result_ids:   list  ← RESERVED for lab linking (1:many)

task_log  [ONE-TO-MANY from batches]
  ├─ id:           str  PRIMARY KEY
  ├─ batch_id:     str  FK → batches.id
  ├─ task_type:    str  ENUM(TASK_TYPES)
  ├─ note:         str
  ├─ logged_by:    str
  ├─ logged_at:    datetime
  ├─ phase_before: str | null
  └─ phase_after:  str | null

FUTURE TABLES (schema-reserved):
  lab_results      → batch_id FK, compound_id, value, unit, lab, date
  batch_passports  → batch_id FK, qr_code_data, issued_at, issued_by
  offline_gps_queue → record_id FK, lat, lng, accuracy, synced bool
        """, language="text")
