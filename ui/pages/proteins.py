import streamlit as st

from services import structures
from ui.components import empty_state, page_header, structure_viewer
from ui.components.submission import submission_card
from ui.footer import render_footer

_TABLE = "protein_table"
_NO_SELECTION = {"selection": {"rows": [], "columns": [], "cells": []}}


def _show_model(entry: dict) -> None:
    title = entry["id"] + (f" · {entry['label']}" if entry.get("label") else "")

    # Default on_dismiss="ignore": closing the dialog does not rerun the app, so nothing behind it reloads.
    @st.dialog(title, width="large", icon=entry.get("icon", ":material/biotech:"))
    def _popup() -> None:
        structure_viewer(**structures.viewer_args(entry), fill=True)
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
    column_config = {
        "Thumbnail": st.column_config.ImageColumn(
            "Structure", width=92, help="PDB structure thumbnail"
        )
    }
    if "RCSB link" in view.columns:
        column_config["RCSB link"] = st.column_config.LinkColumn(
            "RCSB entry", display_text="Open entry ↗", help="Open this structure on RCSB PDB")
    st.dataframe(view, hide_index=True, width="stretch", height="content", row_height=68,
                 column_config=column_config,
                 on_select="rerun", selection_mode="single-cell", key=_TABLE)

    if entry:
        _show_model(entry)


def render() -> None:
    # Give the upload invitation enough width to read as a deliberate hero action.
    hero, submit = st.columns([3, 2.5], vertical_alignment="center")
    with hero:
        page_header("Proteins", "Browse stored structures. Click any row to view its 3D model.")
    with submit:
        submission_card(
            title="Submit a protein model",
            description="Can’t find the structure you need? Request it for comparison in FoldShield.",
            key="proteins_hero_submit",
            button_label="Request upload",
            layout="vertical",
        )

    df = structures.table()
    if df.empty:
        empty_state("No structures yet", "Add entries to PDBs in static/samples.py.")
    else:
        _browser(df)

    submission_card(
        title="Your protein can be part of the comparison",
        description="If the structure you need isn’t listed above, request an upload for FoldShield.",
        key="proteins_footer_submit",
        button_label="Request a comparison",
    )
    render_footer(show_model_request=False)
