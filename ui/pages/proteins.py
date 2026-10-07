import streamlit as st

from services import structures
from ui.components import empty_state, page_header, structure_viewer

_TABLE = "protein_table"
_VERSION = "protein_table_version"


def _table_key() -> str:
    # The key changes after every click. That gives a fresh table with nothing selected, so
    # clicking the same row again (after closing the popup) opens it again.
    return f"{_TABLE}_{st.session_state.get(_VERSION, 0)}"


def _show_model(entry: dict) -> None:
    title = f"{entry['icon']} {entry['id']}" + (f" · {entry['label']}" if entry.get("label") else "")

    @st.dialog(title, width="large", on_dismiss="rerun")
    def _popup() -> None:
        structure_viewer(**structures.viewer_args(entry), height=460)
        for key, value in entry.get("details", {}).items():
            st.caption(f"{key}: {value}")
    _popup()


def render() -> None:
    page_header("Proteins", "Browse stored structures. Click any row to view its 3D model.")
    df = structures.table()
    if df.empty:
        empty_state("No structures yet", "Add entries to PDBs in static/samples.py.")
        return

    query = st.text_input("Search", placeholder="ID, label, protein…")
    view = structures.search(df, query).reset_index(drop=True)
    st.caption(f"{len(view)} of {len(df)} structures")

    # "single-cell" selection = a click anywhere in a row, with no checkbox column.
    event = st.dataframe(view, hide_index=True, width="stretch", height="content", on_select="rerun", selection_mode="single-cell", key=_table_key())

    cells = event.selection.cells
    if cells:
        entry = structures.get(view.iloc[cells[0][0]]["ID"])
        st.session_state[_VERSION] = st.session_state.get(_VERSION, 0) + 1   # next run: unselected table
        if entry:
            _show_model(entry)