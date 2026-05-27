"""
db.py — Barakah Roots Data Layer
=================================
All persistence is JSON-file based (SQLite-ready swap-out path noted below).
Schema is designed for One-to-Many: MotherPlant → Batch → Tasks/LabResults.

Future SQLite migration: replace load/save functions with SQLAlchemy session calls.
Each model dict maps 1:1 to a table row.

TABLE RELATIONSHIPS:
  species_info (existing Excel) ←── mother_plants.species (FK by name)
  mother_plants ←────────────────── batches.mother_plant_id  (1:many)
  batches ←──────────────────────── task_log.batch_id        (1:many)
  batches ←──────────────────────── lab_results.batch_id     (1:many, FUTURE)
  batches ─────────────────────────► batch_passport.batch_id (1:1, FUTURE)
"""

import json
import uuid
import os
from datetime import datetime, date
from typing import Optional

# ── File paths (all data lives in /data/ next to this file) ──────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
MOTHER_PLANTS_FILE = os.path.join(_HERE, "mother_plants.json")
BATCHES_FILE       = os.path.join(_HERE, "batches.json")
TASK_LOG_FILE      = os.path.join(_HERE, "task_log.json")
OFFLINE_QUEUE_FILE = os.path.join(_HERE, "offline_gps_queue.json")
# FUTURE: LAB_RESULTS_FILE = os.path.join(_HERE, "lab_results.json")

# ── Enums (as string constants for JSON portability) ─────────────────────────
GROWTH_PHASES  = ["Germination", "Rapid Growth", "Hardening", "Ready for Field"]
TASK_TYPES     = ["Watering", "Fertilising", "Pest Check", "Phase Change", "Compliance Note", "Other"]
ROLES          = ["admin", "nursery_manager", "field_staff"]
PHENOTYPE_TAGS = ["High Yield", "Disease Resistant", "Drought Tolerant", "High Bioactivity", "Morphological Variant"]

# ── Generic persistence ───────────────────────────────────────────────────────
def _load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def _save(path: str, data: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def _now() -> str:
    return datetime.utcnow().isoformat()

def _uid() -> str:
    return str(uuid.uuid4())[:8].upper()

# ─────────────────────────────────────────────────────────────────────────────
# MODEL: MOTHER PLANT
# ─────────────────────────────────────────────────────────────────────────────
"""
mother_plant {
  id:              str  — e.g. "MP-A3F2"           PRIMARY KEY
  species:         str  — must match species_info key
  phenotype_id:    str  — e.g. "WU-HY-001" (human-readable tag)
  phenotype_tags:  list — subset of PHENOTYPE_TAGS
  location_name:   str  — human label e.g. "Karura Forest, Plot 3"
  gps_lat:         float
  gps_lng:         float
  gps_accuracy_m:  float — metres; reject if > 10m for field use
  gps_captured_at: str  — ISO datetime of GPS capture
  gps_method:      str  — "device" | "manual" | "offline_queue"
  notes:           str
  image_path:      str  — relative path to plant_images/
  registered_by:   str  — username
  registered_at:   str  — ISO datetime
  is_active:       bool — soft delete
}
"""

def get_mother_plants() -> list:
    return _load(MOTHER_PLANTS_FILE)

def get_mother_plant(mp_id: str) -> Optional[dict]:
    return next((m for m in get_mother_plants() if m["id"] == mp_id), None)

def save_mother_plant(mp: dict):
    plants = get_mother_plants()
    existing = next((i for i, m in enumerate(plants) if m["id"] == mp["id"]), None)
    if existing is not None:
        plants[existing] = mp
    else:
        plants.append(mp)
    _save(MOTHER_PLANTS_FILE, plants)

def new_mother_plant(
    species: str,
    phenotype_id: str,
    phenotype_tags: list,
    location_name: str,
    gps_lat: float,
    gps_lng: float,
    gps_accuracy_m: float,
    gps_method: str,
    notes: str,
    registered_by: str,
    image_path: str = "",
) -> dict:
    return {
        "id":              f"MP-{_uid()}",
        "species":         species,
        "phenotype_id":    phenotype_id,
        "phenotype_tags":  phenotype_tags,
        "location_name":   location_name,
        "gps_lat":         gps_lat,
        "gps_lng":         gps_lng,
        "gps_accuracy_m":  gps_accuracy_m,
        "gps_captured_at": _now(),
        "gps_method":      gps_method,
        "notes":           notes,
        "image_path":      image_path,
        "registered_by":   registered_by,
        "registered_at":   _now(),
        "is_active":       True,
        # FUTURE: "passport_qr": None, "lab_result_ids": []
    }

# ─────────────────────────────────────────────────────────────────────────────
# MODEL: BATCH
# ─────────────────────────────────────────────────────────────────────────────
"""
batch {
  id:               str  — e.g. "BAT-9C1A"         PRIMARY KEY
  mother_plant_id:  str  — FK → mother_plants.id
  species:          str  — inherited from mother plant (denormalised for query speed)
  phenotype_id:     str  — inherited
  nursery_location: str  — e.g. "Greenhouse A, Bench 3"
  planting_date:    str  — ISO date
  cutting_count:    int  — number of cuttings/seeds in batch
  growth_phase:     str  — one of GROWTH_PHASES
  compliance_log:   list — list of compliance note strings
  created_by:       str
  created_at:       str
  is_active:        bool
  # FUTURE PASSPORT fields (schema-reserved, null until implemented):
  passport_qr_code: null
  lab_result_ids:   list  — FK list → lab_results.id (1:many, FUTURE)
}
"""

def get_batches() -> list:
    return _load(BATCHES_FILE)

def get_batch(batch_id: str) -> Optional[dict]:
    return next((b for b in get_batches() if b["id"] == batch_id), None)

def get_batches_for_mother(mp_id: str) -> list:
    return [b for b in get_batches() if b["mother_plant_id"] == mp_id]

def save_batch(batch: dict):
    batches = get_batches()
    existing = next((i for i, b in enumerate(batches) if b["id"] == batch["id"]), None)
    if existing is not None:
        batches[existing] = batch
    else:
        batches.append(batch)
    _save(BATCHES_FILE, batches)

def new_batch(
    mother_plant_id: str,
    nursery_location: str,
    planting_date: str,
    cutting_count: int,
    created_by: str,
) -> dict:
    mp = get_mother_plant(mother_plant_id)
    return {
        "id":               f"BAT-{_uid()}",
        "mother_plant_id":  mother_plant_id,
        "species":          mp["species"] if mp else "",
        "phenotype_id":     mp["phenotype_id"] if mp else "",
        "nursery_location": nursery_location,
        "planting_date":    planting_date,
        "cutting_count":    cutting_count,
        "growth_phase":     GROWTH_PHASES[0],
        "compliance_log":   [],
        "created_by":       created_by,
        "created_at":       _now(),
        "is_active":        True,
        # Schema-reserved for future features:
        "passport_qr_code": None,
        "lab_result_ids":   [],
    }

def bulk_update_batches(updated_rows: list):
    """Accept a list of dicts from st.data_editor and persist changes."""
    batches = get_batches()
    index   = {b["id"]: i for i, b in enumerate(batches)}
    for row in updated_rows:
        if row["id"] in index:
            batches[index[row["id"]]].update(row)
    _save(BATCHES_FILE, batches)

# ─────────────────────────────────────────────────────────────────────────────
# MODEL: TASK LOG
# ─────────────────────────────────────────────────────────────────────────────
"""
task_log entry {
  id:          str  PRIMARY KEY
  batch_id:    str  FK → batches.id
  task_type:   str  one of TASK_TYPES
  note:        str
  logged_by:   str
  logged_at:   str  ISO datetime
  phase_before: str | null  (if task_type == "Phase Change")
  phase_after:  str | null
}
"""

def get_task_log(batch_id: str = None) -> list:
    logs = _load(TASK_LOG_FILE)
    if batch_id:
        logs = [l for l in logs if l["batch_id"] == batch_id]
    return sorted(logs, key=lambda x: x["logged_at"], reverse=True)

def log_task(
    batch_id: str,
    task_type: str,
    note: str,
    logged_by: str,
    phase_before: str = None,
    phase_after: str = None,
):
    logs = _load(TASK_LOG_FILE)
    entry = {
        "id":           f"TASK-{_uid()}",
        "batch_id":     batch_id,
        "task_type":    task_type,
        "note":         note,
        "logged_by":    logged_by,
        "logged_at":    _now(),
        "phase_before": phase_before,
        "phase_after":  phase_after,
    }
    logs.append(entry)
    _save(TASK_LOG_FILE, logs)
    # If phase change, update the batch itself
    if task_type == "Phase Change" and phase_after:
        batch = get_batch(batch_id)
        if batch:
            batch["growth_phase"] = phase_after
            batch["compliance_log"].append(f"{_now()[:10]}: Phase → {phase_after} (by {logged_by})")
            save_batch(batch)
    return entry

# ─────────────────────────────────────────────────────────────────────────────
# OFFLINE GPS QUEUE
# ─────────────────────────────────────────────────────────────────────────────
"""
Offline-first strategy:
  1. If GPS capture succeeds → write directly to mother_plant record.
  2. If device is offline OR accuracy > threshold → write to offline_gps_queue.json.
  3. On next connectivity: queue is flushed and merged into the relevant record.
  4. All queue entries carry a 'pending' flag so the UI can show unsynced data.

offline_queue entry {
  id:          str
  record_type: "mother_plant"
  record_id:   str
  field:       "gps_lat" | "gps_lng" | "gps_accuracy_m"
  value:       any
  captured_at: str
  synced:      bool
}
"""

def queue_offline_gps(record_id: str, lat: float, lng: float, accuracy: float):
    queue = _load(OFFLINE_QUEUE_FILE)
    queue.append({
        "id":          _uid(),
        "record_type": "mother_plant",
        "record_id":   record_id,
        "gps_lat":     lat,
        "gps_lng":     lng,
        "gps_accuracy_m": accuracy,
        "captured_at": _now(),
        "synced":      False,
        "gps_method":  "offline_queue",
    })
    _save(OFFLINE_QUEUE_FILE, queue)

def flush_offline_queue() -> int:
    """Merge pending offline GPS entries into mother plant records. Returns count synced."""
    queue  = _load(OFFLINE_QUEUE_FILE)
    synced = 0
    for entry in queue:
        if entry.get("synced"): continue
        mp = get_mother_plant(entry["record_id"])
        if mp:
            mp["gps_lat"]         = entry["gps_lat"]
            mp["gps_lng"]         = entry["gps_lng"]
            mp["gps_accuracy_m"]  = entry["gps_accuracy_m"]
            mp["gps_captured_at"] = entry["captured_at"]
            mp["gps_method"]      = "offline_queue"
            save_mother_plant(mp)
            entry["synced"] = True
            synced += 1
    _save(OFFLINE_QUEUE_FILE, queue)
    return synced

def get_pending_queue() -> list:
    return [e for e in _load(OFFLINE_QUEUE_FILE) if not e.get("synced")]
