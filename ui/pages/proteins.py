import streamlit as st
from services import catalog
from ui.components import empty_state, page_header
from ui.route import go


def render() -> None:
    page_header("Proteins", "Browse stored structures. Select a row to open it.")
    df = catalog.load_catalog()
    if df.empty:
        empty_state("The catalog is empty", f"Add rows to {catalog.CATALOG_PATH.name}.")
        return
    if catalog.is_sample():
        st.caption("Showing sample data. Put your own file at data/catalog.csv "
                   "(needs an id column; pdb_id enables the 3D viewer).")

    f1, f2 = st.columns([2, 1])
    query = f1.text_input("Search", placeholder="Name, ID, PDB code…")
    collections = ()
    if "collection" in df.columns:
        collections = f2.multiselect("Collection", sorted(df["collection"].dropna().unique()))

    view = catalog.search(df, query, collections).reset_index(drop=True)
    st.caption(f"{len(view)} of {len(df)} structures")
    event = st.dataframe(view, hide_index=True, use_container_width=True,
                         on_select="rerun", selection_mode="single-row", key="protein_table")

    rows = event.selection.rows
    if rows:
        pid = str(view.iloc[rows[0]]["id"])
        if st.button(f"Open {pid}", type="primary"):
            go("protein", protein=pid)
