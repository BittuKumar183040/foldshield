import streamlit as st
from ui import route
from ui.components import card_grid, empty_state, page_header, stat_card, structure_viewer
from ui.theme import MUTED
from services import catalog


def _back() -> None:
    if st.button("← Back to proteins"):
        route.go("proteins")


def render() -> None:
    pid = route.param("protein")
    if not pid:
        empty_state("No protein selected", "Pick one from the Proteins page.")
        _back()
        return
    row = catalog.get_protein(pid)
    if row is None:
        st.error(f"No protein with id '{pid}'.")
        _back()
        return

    route.set_param("protein", pid)               # keeps the URL shareable
    _back()
    page_header(str(row.get("name") or pid), f"ID: {pid}")

    left, right = st.columns([3, 2])
    with left:
        structure_viewer(pdb_id=row.get("pdb_id"))
    with right:
        fields = {k: v for k, v in row.items() if k not in ("id", "name")}
        card_grid([stat_card(k.replace("_", " ").title(), v, MUTED, size="sm", center=False)
                   for k, v in fields.items()])
