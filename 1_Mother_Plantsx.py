"""
pages/1_Mother_Plants.py — Mother Plant Registry
=================================================
Roles: admin, nursery_manager → full CRUD
       field_staff             → read-only map view
"""

import streamlit as st
import pandas as pd
import os, sys, base64
from PIL import Image
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from components.auth import require_login, can, current_user, ROLE_LABELS
from components.gps  import gps_capture_widget
from data.db import (
    get_mother_plants, save_mother_plant, new_mother_plant,
    get_batches_for_mother, PHENOTYPE_TAGS,
)

# ── Load species list from main app data ──────────────────────────────────────
@st.cache_data
def load_species():
    try:
        df = pd.read_excel("kenyan_compounds.xlsx", sheet_name="molecules (1)")
        df = df.dropna(subset=["Compound Name"])
        rows = []
        for _, row in df.iterrows():
            sp = row.get("Species","")
            if pd.notna(sp):
                rows.extend([x.strip() for x in str(sp).split(";")])
        return sorted(set(rows))
    except Exception:
        return ["Warburgia ugandensis", "Erythrina abyssinica", "Aloe secundiflora"]

require_login()
user = current_user()
species_list = load_species()
plants = get_mother_plants()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,600&family=Inter:wght@300;400;500&display=swap');
html,body,[class*="css"],.stApp { font-family:'Inter',sans-serif; background:#f7f4ee !important; }
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding:2rem 3rem !important; max-width:1100px !important; }
.page-title { font-family:'Cormorant Garamond',serif; font-size:2.2rem; font-weight:600; color:#1c3d20; font-style:italic; margin-bottom:0.2rem; }
.page-sub { font-size:0.8rem; color:#9a9080; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:2rem; }
.mp-card { background:#fff; border:1.5px solid #e0dbd0; border-radius:16px; padding:1.2rem 1.4rem; margin-bottom:12px; }
.mp-id { font-size:0.7rem; font-weight:600; color:#9a9080; letter-spacing:0.1em; }
.mp-name { font-family:'Cormorant Garamond',serif; font-size:1.2rem; font-style:italic; color:#1c3d20; font-weight:600; margin:2px 0; }
.mp-loc { font-size:0.78rem; color:#7a8a7a; }
.tag { font-size:0.63rem; padding:2px 8px; border-radius:20px; background:#eef6ee; color:#2c5e2e; border:1px solid #d0e8d0; font-weight:500; display:inline-block; margin:2px; }
.acc-good { color:#2c5e2e; font-weight:600; }
.acc-warn { color:#b85c00; font-weight:600; }
.stTabs [data-baseweb="tab"] { font-family:'Inter',sans-serif; }
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="page-title">Mother Plant Registry</div>', unsafe_allow_html=True)
st.markdown(f'<div class="page-sub">Elite genetic sources · {len(plants)} registered · {ROLE_LABELS.get(user["role"])}</div>', unsafe_allow_html=True)

tabs = ["🗺️ Map View", "📋 Registry"] + (["➕ Register New"] if can("create_mother_plant") else [])
tab_objs = st.tabs(tabs)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: MAP VIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab_objs[0]:
    if not plants:
        st.info("No mother plants registered yet. Register the first one in the 'Register New' tab.")
    else:
        try:
            import folium
            from streamlit_folium import st_folium

            # Centre map on mean of all points, fallback to Nairobi
            lats = [p["gps_lat"] for p in plants if p.get("gps_lat")]
            lngs = [p["gps_lng"] for p in plants if p.get("gps_lng")]
            centre = (sum(lats)/len(lats), sum(lngs)/len(lngs)) if lats else (-1.2921, 36.8219)

            m = folium.Map(location=centre, zoom_start=10, tiles="OpenStreetMap")

            for p in plants:
                if not p.get("gps_lat"): continue
                acc = p.get("gps_accuracy_m", 999)
                colour = "green" if acc <= 15 else "orange"
                batches = get_batches_for_mother(p["id"])

                popup_html = f"""
                <div style="font-family:sans-serif;min-width:200px">
                  <b style="color:#1c3d20">{p['species']}</b><br>
                  <span style="color:#888;font-size:11px">{p['id']} · {p['phenotype_id']}</span><br><br>
                  <b>Location:</b> {p.get('location_name','—')}<br>
                  <b>GPS:</b> {p['gps_lat']:.5f}, {p['gps_lng']:.5f}<br>
                  <b>Accuracy:</b> {acc:.1f}m<br>
                  <b>Batches:</b> {len(batches)}<br>
                  <b>Tags:</b> {', '.join(p.get('phenotype_tags',[])) or '—'}
                </div>
                """
                folium.Marker(
                    location=[p["gps_lat"], p["gps_lng"]],
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"{p['species']} ({p['id']})",
                    icon=folium.Icon(color=colour, icon="leaf", prefix="fa"),
                ).add_to(m)

                # Accuracy circle
                folium.Circle(
                    location=[p["gps_lat"], p["gps_lng"]],
                    radius=max(acc, 5),
                    color=colour, fill=True, fill_opacity=0.1,
                ).add_to(m)

            st_folium(m, width=None, height=500, returned_objects=[])
            st.caption("🟢 High accuracy (≤15m)  🟠 Low accuracy (>15m) — click markers for details")

        except ImportError:
            st.warning("Install `folium` and `streamlit-folium` for the map view: `pip install folium streamlit-folium`")
            # Fallback: show coordinates as table
            map_data = pd.DataFrame([
                {"ID": p["id"], "Species": p["species"], "Lat": p.get("gps_lat"), "Lng": p.get("gps_lng"), "Accuracy (m)": p.get("gps_accuracy_m")}
                for p in plants if p.get("gps_lat")
            ])
            st.dataframe(map_data, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: REGISTRY LIST
# ─────────────────────────────────────────────────────────────────────────────
with tab_objs[1]:
    if not plants:
        st.info("No mother plants registered yet.")
    else:
        # Filters
        fc1, fc2 = st.columns(2)
        with fc1:
            filter_sp = st.selectbox("Filter by species", ["All"] + sorted(set(p["species"] for p in plants)))
        with fc2:
            filter_tag = st.selectbox("Filter by trait", ["All"] + PHENOTYPE_TAGS)

        filtered = plants
        if filter_sp != "All":   filtered = [p for p in filtered if p["species"] == filter_sp]
        if filter_tag != "All":  filtered = [p for p in filtered if filter_tag in p.get("phenotype_tags", [])]

        st.markdown(f"**{len(filtered)}** mother plant(s) shown")

        for p in filtered:
            batches = get_batches_for_mother(p["id"])
            acc = p.get("gps_accuracy_m", 999)
            acc_class = "acc-good" if acc <= 15 else "acc-warn"
            tags_html = " ".join(f'<span class="tag">{t}</span>' for t in p.get("phenotype_tags", []))

            with st.expander(f"🌿 {p['species']} · {p['id']} · {p.get('location_name','')}", expanded=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"""
                    <div class="mp-id">{p['id']} · Registered {p['registered_at'][:10]}</div>
                    <div class="mp-name">{p['species']}</div>
                    <div class="mp-loc">📍 {p.get('location_name','—')} &nbsp;|&nbsp;
                        {p['gps_lat']:.5f}, {p['gps_lng']:.5f} &nbsp;|&nbsp;
                        <span class="{acc_class}">{acc:.1f}m accuracy</span>
                    </div>
                    <div style="margin:8px 0">{tags_html}</div>
                    <div style="font-size:0.82rem;color:#4a5a4a;margin-top:4px">
                        <b>Phenotype ID:</b> {p['phenotype_id']}<br>
                        <b>Batches derived:</b> {len(batches)}<br>
                        <b>GPS method:</b> {p.get('gps_method','—')}<br>
                        <b>Notes:</b> {p.get('notes','—')}
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    img_path = p.get("image_path","")
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.markdown('<div style="background:#f0f7f0;border-radius:12px;height:140px;display:flex;align-items:center;justify-content:center;color:#9abc9a;font-size:2rem;border:2px dashed #c5dfc5">🌿</div>', unsafe_allow_html=True)

                if batches:
                    st.caption(f"Batches: {', '.join(b['id'] for b in batches)}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB: REGISTER NEW (admin / nursery_manager only)
# ─────────────────────────────────────────────────────────────────────────────
if can("create_mother_plant"):
    with tab_objs[2]:
        st.markdown("#### Register Elite Mother Plant")
        st.caption("All fields required. GPS accuracy must be under 15m for field deployment.")

        with st.form("register_mother_plant", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                species = st.selectbox("Species *", species_list)
                phenotype_id = st.text_input("Phenotype ID *", placeholder="e.g. WU-HY-001")
                location_name = st.text_input("Location Name *", placeholder="e.g. Karura Forest, Plot 3")
            with fc2:
                phenotype_tags = st.multiselect("Phenotype Traits", PHENOTYPE_TAGS)
                notes = st.text_area("Notes", height=100, placeholder="Observed characteristics, collection context…")

            st.markdown("---")
            # GPS inputs inside form (geolocation widget can't be inside form, so manual only here)
            st.markdown("**GPS Coordinates** — enter coordinates from your GPS device or Google Maps")
            gc1, gc2, gc3 = st.columns(3)
            with gc1: gps_lat = st.number_input("Latitude *",  value=-1.2921, format="%.6f")
            with gc2: gps_lng = st.number_input("Longitude *", value=36.8219, format="%.6f")
            with gc3: gps_acc = st.number_input("Accuracy (m) *", value=5.0, min_value=0.1)
            gps_method = st.selectbox("GPS Method", ["manual", "device", "offline_queue"])

            st.markdown("---")
            st.markdown("**Plant Photo** (optional)")
            uploaded_img = st.file_uploader("Upload photo", type=["jpg","jpeg","png"])

            submitted = st.form_submit_button("✅ Register Mother Plant", use_container_width=True)

            if submitted:
                errors = []
                if not species:         errors.append("Species required")
                if not phenotype_id:    errors.append("Phenotype ID required")
                if not location_name:   errors.append("Location name required")
                if gps_acc > 50:        errors.append("GPS accuracy too poor (>50m). Re-capture or verify coordinates.")

                if errors:
                    for e in errors: st.error(e)
                else:
                    mp = new_mother_plant(
                        species=species,
                        phenotype_id=phenotype_id,
                        phenotype_tags=phenotype_tags,
                        location_name=location_name,
                        gps_lat=gps_lat,
                        gps_lng=gps_lng,
                        gps_accuracy_m=gps_acc,
                        gps_method=gps_method,
                        notes=notes,
                        registered_by=user["username"],
                    )
                    # Save image if provided
                    if uploaded_img:
                        img_dir = os.path.join("plant_images", mp["id"])
                        os.makedirs(img_dir, exist_ok=True)
                        img_path = os.path.join(img_dir, "mother_plant.jpg")
                        img = Image.open(uploaded_img).convert("RGB")
                        img.save(img_path, "JPEG", quality=85)
                        mp["image_path"] = img_path

                    save_mother_plant(mp)
                    st.success(f"✅ Registered **{mp['id']}** — {species} at {location_name}")
                    st.rerun()

        # Live GPS capture (outside form, for device GPS)
        if st.checkbox("📱 Capture GPS from device (outside form)"):
            result = gps_capture_widget(key_prefix="reg_live")
            if result:
                st.info(f"Got fix: {result['lat']:.6f}, {result['lng']:.6f} ± {result['accuracy_m']:.1f}m — copy these into the form above.")
