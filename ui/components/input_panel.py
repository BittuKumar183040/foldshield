"""Inputs for the Analyze page, laid out on the page itself (no sidebar).

Reference and Query each get a card. The card's "Choose" button opens the structure picker
dialog (ui/components/structure_dialog.py), which lists the structures in static/samples.py (PDBs).

The other card's selection shapes the list:
  * the structure already chosen on the other side is left out
  * its `recommendation` ids are moved to the top under a "Recommended" heading
"""
from dataclasses import dataclass
from typing import Any

import streamlit as st

from services import structures
from services.inputs import PdbInput, detect_chains
from static.samples import PDBs
from ui.components.cards import section
from ui.components.structure_dialog import details_text, open_structure_dialog, short_text

# slot -> (title, data)
SLOTS = {"ref": ("Reference", PDBs), "query": ("Query", PDBs)}


@dataclass
class AnalyzeInputs:
    ref: PdbInput
    query: PdbInput
    ref_chain: str
    query_chain: str
    mode: str
    keep_hetatm: bool
    summary_upload: Any
    run_clicked: bool


# --------------------------------------------------------------------------- data
def _other(slot: str) -> str:
    return "query" if slot == "ref" else "ref"


def _pick_key(slot: str) -> str:
    return f"analyze_pick_{slot}"


def _selected_entry(slot: str) -> dict | None:
    return SLOTS[slot][1].get(st.session_state.get(_pick_key(slot)))


@st.cache_data(show_spinner=False)
def _chains(path: str, mtime: float):
    return detect_chains(path)                      # (chain_ids, error message)


def _resolve(entry: dict | None) -> PdbInput:
    if entry is None:
        return PdbInput()
    path = structures.find_pdb(entry)
    if path is None:
        return PdbInput(fp=entry["id"], name=entry["id"],
                        error=f"PDB file for {entry['id']} not found. Expected {entry['path']}.")
    chains, err = _chains(str(path), path.stat().st_mtime)
    return PdbInput(path=str(path), chains=chains, fp=entry["id"], name=entry["id"], error=err)


# --------------------------------------------------------------------------- picker
def _open_chooser(slot: str) -> None:
    title, data = SLOTS[slot]
    other = _selected_entry(_other(slot))

    def _chosen(pdb_id: str) -> None:
        st.session_state[_pick_key(slot)] = pdb_id

    open_structure_dialog(
        key=slot,
        title=f"Choose {title.lower()}",
        entries=data,
        exclude=other["id"] if other else None,
        recommended=other.get("recommendation", []) if other else [],
        recommended_label=f"Recommended for {other['id']}" if other else None,
        on_choose=_chosen,
    )


# --------------------------------------------------------------------------- cards
def _chain_picker(label: str, slot: str, pdb: PdbInput) -> str:
    key = f"chain_{slot}_{pdb.fp}"          # new structure -> fresh widget state
    if not pdb.ready:
        st.selectbox(label, ["—"], disabled=True, key=key)
        return "A"
    if pdb.chains:
        return st.selectbox(label, pdb.chains, key=key)
    return st.text_input(label, value="A", key=key)


def _structure_card(slot: str) -> tuple[PdbInput, str]:
    title = SLOTS[slot][0]
    entry = _selected_entry(slot)
    pdb = _resolve(entry)

    with st.container(border=True):
        head, action = st.columns([3, 1.2], vertical_alignment="center")
        head.markdown(f"**{title}**")
        if action.button("Choose", key=f"analyze_toggle_{slot}", use_container_width=True):
            _open_chooser(slot)

        if entry:
            st.markdown(f"{entry['icon']}  **{entry['id']}**  \n:small[{short_text(entry.get('label'), 60)}]")
            if details_text(entry):
                st.caption(details_text(entry))
        else:
            st.caption("Nothing selected yet.")
        if pdb.error:
            st.warning(pdb.error)
        chain = _chain_picker(f"{title} chain", slot, pdb)
    return pdb, chain


# --------------------------------------------------------------------------- panel
def render_inputs() -> AnalyzeInputs:
    with st.container(border=True):
        section("Inputs", "Choose a reference and a query structure, pick their chains, then run.")

        col_ref, col_query = st.columns(2)
        with col_ref:
            ref, ref_chain = _structure_card("ref")
        with col_query:
            query, query_chain = _structure_card("query")

        opt_mode, opt_het, opt_run = st.columns([2, 1.5, 1.5], vertical_alignment="bottom")
        with opt_mode:
            mode = st.radio("Coordinate mode", ["ca", "sequence"], index=0, horizontal=True)
        with opt_het:
            keep_hetatm = st.checkbox("Keep HETATM", value=False)
        with opt_run:
            ready = ref.ready and query.ready
            run = st.button("Run pipeline", type="primary", use_container_width=True,
                            disabled=not ready,
                            help=None if ready else "Choose a reference and a query structure first.")

        with st.expander("Load a saved run"):
            summary_upload = st.file_uploader("summary.json", type=["json"], key="upload_summary")

    return AnalyzeInputs(ref, query, ref_chain, query_chain, mode, keep_hetatm, summary_upload, run)