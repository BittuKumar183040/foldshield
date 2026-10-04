"""Stored structures shown on the Proteins pages.

Replace the source by dropping your own CSV at data/catalog.csv (or set FOLDSHIELD_CATALOG).
Required column: id.  Optional: pdb_id (enables the 3D viewer), name, collection.
Any other columns are shown automatically in the table and on the detail page.
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

CATALOG_PATH = Path(os.environ.get("FOLDSHIELD_CATALOG",
                                   Path(__file__).resolve().parents[1] / "data" / "catalog.csv"))

_SAMPLE = [
    {"id": "ubq",  "name": "Ubiquitin",              "pdb_id": "1UBQ", "collection": "Demo set A", "length": 76},
    {"id": "hewl", "name": "Hen egg-white lysozyme", "pdb_id": "1LYZ", "collection": "Demo set A", "length": 129},
    {"id": "crn",  "name": "Crambin",                "pdb_id": "1CRN", "collection": "Demo set A", "length": 46},
    {"id": "mb",   "name": "Sperm whale myoglobin",  "pdb_id": "1MBN", "collection": "Demo set B", "length": 153},
    {"id": "bn",   "name": "Barnase",                "pdb_id": "1BNI", "collection": "Demo set B", "length": 110},
    {"id": "t4l",  "name": "T4 lysozyme",            "pdb_id": "2LZM", "collection": "Demo set B", "length": 164},
]


def is_sample() -> bool:
    return not CATALOG_PATH.exists()


@st.cache_data(show_spinner=False)
def load_catalog() -> pd.DataFrame:
    df = pd.DataFrame(_SAMPLE) if is_sample() else pd.read_csv(CATALOG_PATH, dtype={"id": str})
    if "id" not in df.columns:
        raise ValueError(f"{CATALOG_PATH} needs an 'id' column.")
    return df


def search(df: pd.DataFrame, query: str = "", collections=()) -> pd.DataFrame:
    if query:
        hit = df.astype(str).apply(lambda c: c.str.contains(query, case=False, regex=False)).any(axis=1)
        df = df[hit]
    if collections and "collection" in df.columns:
        df = df[df["collection"].isin(collections)]
    return df


def get_protein(pid: str) -> dict | None:
    df = load_catalog()
    rows = df[df["id"].astype(str) == str(pid)]
    return None if rows.empty else rows.iloc[0].dropna().to_dict()
