"""
pages/2_Batches.py — Batch Management & Task Logger
=====================================================
Roles: admin/nursery_manager → create batches, bulk edit, log tasks
       field_staff           → log tasks only (no create/bulk edit)
"""

import streamlit as st
import pandas as pd
import os, sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from components.auth import require_login, can, current_user, ROLE_LABELS
from data.db import (
    get_batches, get_batch, save_batch, new_batch, bulk_update_batches,
    get_mother_plants, get_mother_plant, log_task, get_task_log,
    GROWTH_PHASES, TASK_TYPES,
)

require_login()
user    = current_user()
batches = get_batches()
mothers = get_mother_plants()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,600&family=Inter:wght@300;400;500&display=swap');
html,body,[class*="css"],.stApp { font-family:'Inter',sans-serif; background:#f7f4ee !important; }
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding:2rem 3rem !important; max-width:1100px !important; }
.page-title { font-family:'Cormorant Garamond',serif; font-size:2.2rem; font-weight:600; color:#1c3d20; font-style:italic; margin-bottom:0.2rem; }
.page-sub { font-size:0.8rem; color:#9a9080; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:2rem; }
.phase-badge { display:inline-block; border-radius:20px; padding:3px 12px; font-size:0.72rem; font-weight:600; }
.phase-Germination { background:#fff8e1; color:#b85c00; border:1px solid #ffd54f; }
.phase-Rapid.Growth { background:#e8f5e9; color:#2e7d32; border:1px solid #a5d6a7; }
.phase-Hardening { background:#e3f2fd; color:#1565c0; border:1px solid #90caf9; }
.phase-Ready.for.Field { background:#f3e5f5; color:#6a1b9a; border:1px solid #ce93d8; }
.task-row { background:#fff; border-radius:10px; padding:0.7rem 1rem; margin-bottom:6px; border:1px solid #e8e2d8; font-size:0.83rem; }
.task-type { font-weight:600; color:#1c3d20; }
.task-meta { color:#9a9080; font-size:0.75rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Nursery Batches</div>', unsafe_allow_html=True)
st.markdown(f'<div class="page-sub">{len(batches)} active batches · {ROLE_LABELS.get(user["role"])}</div>', unsafe_allow_html=True)

tabs = ["📊 Dashboard", "📝 Task Logger"]
if can("create_batch"):    tabs.append("➕ New Batch")
if can("bulk_edit_batches"): tabs.append("✏️ Bulk Editor")
tab_objs = st.tabs(tabs)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: DASHBOARD / INVENTORY VIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab_objs[0]:
    if not batches:
        st.info("No batches yet. Create the first batch in the 'New Batch' tab.")
    else:
        # KPI row
        active = [b for b in batches if b.get("is_active")]
        phase_counts = {p: len([b for b in active if b["growth_phase"] == p]) for p in GROWTH_PHASES}
        total_cuttings = sum(b.get("cutting_count", 0) for b in active)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Batches",     len(active))
        k2.metric("Total Cuttings",    total_cuttings)
        k3.metric("Germination",       phase_counts.get("Germination", 0))
        k4.metric("Rapid Growth",      phase_counts.get("Rapid Growth", 0))
        k5.metric("Ready for Field",   phase_counts.get("Ready for Field", 0))

        st.divider()

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            species_options = ["All"] + sorted(set(b["species"] for b in active))
            f_species = st.selectbox("Genetic Source (Species)", species_options)
        with fc2:
            f_phase = st.selectbox("Growth Phase", ["All"] + GROWTH_PHASES)
        with fc3:
            mp_options = {"All": "All"}
            for mp in mothers: mp_options[mp["id"]] = f"{mp['id']} — {mp['species']}"
            f_mp = st.selectbox("Mother Plant", list(mp_options.keys()),
                                format_func=lambda k: mp_options[k])

        filtered = active
        if f_species != "All": filtered = [b for b in filtered if b["species"] == f_species]
        if f_phase   != "All": filtered = [b for b in filtered if b["growth_phase"] == f_phase]
        if f_mp      != "All": filtered = [b for b in filtered if b["mother_plant_id"] == f_mp]

        st.markdown(f"**{len(filtered)}** batch(es) shown")

        for b in filtered:
            mp = get_mother_plant(b["mother_plant_id"])
            tasks = get_task_log(b["id"])
            phase = b["growth_phase"]
            phase_cls = phase.replace(" ", ".")

            with st.expander(f"🌱 {b['id']} · {b['species']} · {phase}", expanded=False):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"""
                    <div style="font-size:0.7rem;color:#9a9080;letter-spacing:0.08em">{b['id']}</div>
                    <div style="font-family:'Cormorant Garamond',serif;font-size:1.2rem;font-style:italic;color:#1c3d20;font-weight:600">{b['species']}</div>
                    <div style="font-size:0.8rem;color:#4a5a4a;margin:4px 0">
                        <b>Phenotype:</b> {b['phenotype_id']} &nbsp;|&nbsp;
                        <b>Mother Plant:</b> {b['mother_plant_id']}<br>
                        <b>Nursery:</b> {b['nursery_location']}<br>
                        <b>Planted:</b> {b['planting_date'][:10]} &nbsp;|&nbsp;
                        <b>Cuttings:</b> {b['cutting_count']}<br>
                        <b>Tasks logged:</b> {len(tasks)}
                    </div>
                    """, unsafe_allow_html=True)
                    if b.get("compliance_log"):
                        st.caption("Compliance: " + " → ".join(b["compliance_log"][-2:]))
                    # Future passport placeholder
                    if b.get("passport_qr_code"):
                        st.image(b["passport_qr_code"], width=80, caption="Batch Passport")
                    else:
                        st.caption("🎫 Batch passport: not yet generated *(future feature)*")
                with c2:
                    # Phase progress indicator
                    pi = GROWTH_PHASES.index(phase) if phase in GROWTH_PHASES else 0
                    for i, p in enumerate(GROWTH_PHASES):
                        dot = "🟢" if i < pi else ("🔵" if i == pi else "⚪")
                        st.caption(f"{dot} {p}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB: TASK LOGGER
# ─────────────────────────────────────────────────────────────────────────────
with tab_objs[1]:
    if not batches:
        st.info("No batches to log tasks against yet.")
    else:
        st.markdown("#### Log a Task")
        batch_options = {b["id"]: f"{b['id']} — {b['species']} ({b['growth_phase']})" for b in batches if b.get("is_active")}

        with st.form("task_logger"):
            sel_batch_id = st.selectbox(
                "Select Batch *",
                list(batch_options.keys()),
                format_func=lambda k: batch_options[k],
            )
            tc1, tc2 = st.columns(2)
            with tc1:
                task_type = st.selectbox("Task Type *", TASK_TYPES)
            with tc2:
                # Phase change fields (only relevant if task_type == Phase Change)
                new_phase = st.selectbox("New Phase (if Phase Change)", GROWTH_PHASES)

            task_note = st.text_area("Notes / Observations *", height=100,
                                     placeholder="e.g. 12 of 40 cuttings showing root emergence. Watered at 7am.")
            submitted = st.form_submit_button("📝 Log Task", use_container_width=True)

            if submitted:
                if not task_note.strip():
                    st.error("Please enter a note.")
                else:
                    current_batch = get_batch(sel_batch_id)
                    phase_before = current_batch["growth_phase"] if task_type == "Phase Change" else None
                    phase_after  = new_phase if task_type == "Phase Change" else None
                    log_task(
                        batch_id=sel_batch_id,
                        task_type=task_type,
                        note=task_note,
                        logged_by=user["username"],
                        phase_before=phase_before,
                        phase_after=phase_after,
                    )
                    st.success(f"✅ Task logged for {sel_batch_id}")
                    st.rerun()

        # Recent task log
        st.divider()
        st.markdown("#### Recent Activity")
        from data.db import get_task_log as get_all_tasks
        recent = get_all_tasks()[:20]
        if recent:
            for t in recent:
                batch_label = batch_options.get(t["batch_id"], t["batch_id"])
                phase_note  = f" → *{t['phase_after']}*" if t.get("phase_after") else ""
                st.markdown(f"""
                <div class="task-row">
                  <span class="task-type">{t['task_type']}{phase_note}</span>
                  &nbsp;·&nbsp;<span style="color:#4a5a4a">{t['batch_id']}</span><br>
                  <span style="color:#3a4a3a;font-size:0.82rem">{t['note']}</span><br>
                  <span class="task-meta">by {t['logged_by']} · {t['logged_at'][:16].replace('T',' ')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No tasks logged yet.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB: NEW BATCH
# ─────────────────────────────────────────────────────────────────────────────
if can("create_batch"):
    with tab_objs[tabs.index("➕ New Batch")]:
        if not mothers:
            st.warning("No mother plants registered yet. Register at least one in the Mother Plants page first.")
        else:
            st.markdown("#### Create New Nursery Batch")
            st.caption("Each batch inherits genetic properties from its selected Mother Plant.")

            mp_map = {mp["id"]: mp for mp in mothers}

            with st.form("new_batch_form", clear_on_submit=True):
                mp_id = st.selectbox(
                    "Mother Plant *",
                    list(mp_map.keys()),
                    format_func=lambda k: f"{k} — {mp_map[k]['species']} ({mp_map[k]['phenotype_id']})",
                )

                bc1, bc2 = st.columns(2)
                with bc1:
                    nursery_loc  = st.text_input("Nursery Location *", placeholder="e.g. Greenhouse A, Bench 3")
                    cutting_count = st.number_input("Number of cuttings/seeds *", min_value=1, value=40)
                with bc2:
                    planting_date = st.date_input("Planting Date *", value=date.today())

                compliance_note = st.text_input(
                    "Initial Compliance Note",
                    placeholder="e.g. Cuttings taken from healthy apical shoot, 10cm length, hormone treated",
                )

                # Show inherited properties preview
                if mp_id:
                    mp = mp_map[mp_id]
                    st.info(
                        f"**Inherited from {mp_id}:** Species: *{mp['species']}* · "
                        f"Phenotype: {mp['phenotype_id']} · "
                        f"Traits: {', '.join(mp.get('phenotype_tags',[]) or ['—'])}"
                    )

                submitted = st.form_submit_button("🌱 Create Batch", use_container_width=True)

                if submitted:
                    errors = []
                    if not nursery_loc: errors.append("Nursery location required")
                    if errors:
                        for e in errors: st.error(e)
                    else:
                        batch = new_batch(
                            mother_plant_id=mp_id,
                            nursery_location=nursery_loc,
                            planting_date=str(planting_date),
                            cutting_count=int(cutting_count),
                            created_by=user["username"],
                        )
                        if compliance_note:
                            batch["compliance_log"].append(f"{date.today()}: {compliance_note} (by {user['username']})")
                        save_batch(batch)
                        st.success(f"✅ Batch **{batch['id']}** created — {batch['species']} × {cutting_count} cuttings")
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB: BULK EDITOR
# ─────────────────────────────────────────────────────────────────────────────
if can("bulk_edit_batches"):
    with tab_objs[tabs.index("✏️ Bulk Editor")]:
        st.markdown("#### Bulk Status Update")
        st.caption("Edit Growth Phase and Nursery Location directly in the table. Click **Save Changes** when done.")

        if not batches:
            st.info("No batches to edit yet.")
        else:
            edit_df = pd.DataFrame([
                {
                    "id":               b["id"],
                    "species":          b["species"],
                    "phenotype_id":     b["phenotype_id"],
                    "mother_plant_id":  b["mother_plant_id"],
                    "nursery_location": b["nursery_location"],
                    "growth_phase":     b["growth_phase"],
                    "cutting_count":    b["cutting_count"],
                    "planting_date":    b["planting_date"][:10],
                    "is_active":        b["is_active"],
                }
                for b in batches
            ])

            edited = st.data_editor(
                edit_df,
                column_config={
                    "id":               st.column_config.TextColumn("Batch ID", disabled=True),
                    "species":          st.column_config.TextColumn("Species", disabled=True),
                    "phenotype_id":     st.column_config.TextColumn("Phenotype", disabled=True),
                    "mother_plant_id":  st.column_config.TextColumn("Mother Plant", disabled=True),
                    "nursery_location": st.column_config.TextColumn("Nursery Location"),
                    "growth_phase":     st.column_config.SelectboxColumn("Growth Phase", options=GROWTH_PHASES),
                    "cutting_count":    st.column_config.NumberColumn("Cuttings", min_value=1),
                    "planting_date":    st.column_config.TextColumn("Planted", disabled=True),
                    "is_active":        st.column_config.CheckboxColumn("Active"),
                },
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
            )

            if st.button("💾 Save Changes", type="primary"):
                bulk_update_batches(edited.to_dict("records"))
                st.success("✅ Batch records updated.")
                st.rerun()
