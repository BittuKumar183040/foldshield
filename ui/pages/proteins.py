import streamlit as st

from services import structures
from ui.components import empty_state, page_header, structure_viewer

_TABLE = "protein_table"
_NO_SELECTION = {"selection": {"rows": [], "columns": [], "cells": []}}


def _show_model(entry: dict) -> None:
    title = f"{entry['icon']} {entry['id']}" + (f" · {entry['label']}" if entry.get("label") else "")

    # Default on_dismiss="ignore": closing the dialog does not rerun the app, so nothing behind it reloads.
    @st.dialog(title, width="large")
    def _popup() -> None:
        structure_viewer(**structures.viewer_args(entry), fill=True)
        for key, value in entry.get("details", {}).items():
            st.caption(f"{key}: {value}")
    _popup()


@st.fragment
def _browser(df) -> None:
    # A fragment: clicking a row (or typing in the search) reruns only this block, not the whole page.
    query = st.text_input("Search", placeholder="ID, label, protein…")
    view = structures.search(df, query).reset_index(drop=True)
    st.caption(f"{len(view)} of {len(df)} structures")
    cells = (st.session_state.get(_TABLE) or {}).get("selection", {}).get("cells", [])
    entry = None
    if cells and cells[0][0] < len(view):
        entry = structures.get(view.iloc[cells[0][0]]["ID"])
    if cells:
        st.session_state[_TABLE] = _NO_SELECTION

    # "single-cell" selection = a click anywhere in a row, with no checkbox column.
    st.dataframe(view, hide_index=True, width="stretch", height="content",
                 on_select="rerun", selection_mode="single-cell", key=_TABLE)

    if entry:
        _show_model(entry)


def render() -> None:
    page_header("Proteins", "Browse stored structures. Click any row to view its 3D model.")
    df = structures.table()
    if df.empty:
        empty_state("No structures yet", "Add entries to PDBs in static/samples.py.")
        return
    _browser(df)