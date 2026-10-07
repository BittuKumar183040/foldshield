"""Structures shown on the Proteins pages. Source of truth: static/samples.py -> PDBs.

Replaces services/catalog.py. To add or edit a structure, edit PDBs in samples.py.
The 3D model comes from the entry's local .pdb file (its `path`, or results/*/<id>.pdb);
if no file exists, the model is downloaded from RCSB by PDB code.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from static.samples import PDBs

ROOT = Path(__file__).resolve().parents[1]          # project root


# --------------------------------------------------------------------------- lookup
def get(pdb_id) -> dict | None:
    return PDBs.get(str(pdb_id).strip().upper())


def recommended(entry: dict) -> list[dict]:
    """Entries listed in this entry's `recommendation` (unknown ids are skipped)."""
    return [PDBs[r] for r in entry.get("recommendation", []) if r in PDBs]


# --------------------------------------------------------------------------- 3D model
def _usable(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0      # an empty file is treated as missing


def find_pdb(entry: dict) -> Path | None:
    path = ROOT / entry["path"]
    if _usable(path):
        return path
    hits = [p for p in sorted(ROOT.glob(f"results/*/{entry['id']}.pdb")) if _usable(p)]
    return hits[0] if hits else None


@st.cache_data(show_spinner=False)
def _read(path: str, mtime: float) -> str:          # mtime in the key: edits to the file show up
    return Path(path).read_text(encoding="utf-8", errors="replace")

def viewer_args(entry: dict) -> dict:
    path = find_pdb(entry)
    if path is None:
        return {}
    return {"pdb_text": _read(str(path), path.stat().st_mtime)}

def model_source(entry: dict) -> str:
    path = find_pdb(entry)
    return f"Local file ({path.relative_to(ROOT).as_posix()})" if path else "RCSB PDB (downloaded)"

# --------------------------------------------------------------------------- table
def table() -> pd.DataFrame:
    rows = []
    for e in PDBs.values():
        row = {"ID": e["id"], "Label": e.get("label") or ""}
        row.update(e.get("details", {}))             # Protein, plus any keys you add later
        row["Recommended"] = ", ".join(r for r in e.get("recommendation", []) if r)
        rows.append(row)
    df = pd.DataFrame(rows).fillna("")
    return df[[c for c in df.columns if c != "Recommended"] + ["Recommended"]]


def search(df: pd.DataFrame, query: str = "") -> pd.DataFrame:
    if not query:
        return df
    hit = df.astype(str).apply(lambda c: c.str.contains(query, case=False, regex=False)).any(axis=1)
    return df[hit]
