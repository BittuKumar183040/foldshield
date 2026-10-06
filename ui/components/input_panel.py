"""Inputs for the Analyze page, laid out on the page itself (no sidebar).

Reference and Query each get a card. The card's "Choose" button opens a compact row of
selectable chips (one per structure, from static/samples.py REFERENCES / QUERIES).
Picking a chip selects it and closes the row; the chain picker sits under it.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from services.inputs import PdbInput, detect_chains
from static.samples import PDBs
from ui.components.cards import section

ROOT = Path(__file__).resolve().parents[2]          # project root

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
def _pick_key(slot: str) -> str:
    return f"analyze_pick_{slot}"


def _open_key(slot: str) -> str:
    return f"analyze_open_{slot}"


def _selected_entry(slot: str) -> dict | None:
    return SLOTS[slot][1].get(st.session_state.get(_pick_key(slot)))


def _find_pdb(entry: dict) -> Path | None:
    path = ROOT / entry["path"]
    if path.exists():
        return path
    hits = sorted(ROOT.glob(f"results/*/{entry['id']}.pdb"))   # fall back to a result folder
    return hits[0] if hits else None


@st.cache_data(show_spinner=False)
def _chains(path: str, mtime: float):
    return detect_chains(path)                      # (chain_ids, error message)


def _details_text(entry: dict) -> str:
    return "  ·  ".join(f"{k}: {v}" for k, v in entry.get("details", {}).items())


def _chip_text(entry: dict) -> str:
    return f"{entry['icon']} {entry['label']}"


def _resolve(entry: dict | None) -> PdbInput:
    if entry is None:
        return PdbInput()
    path = _find_pdb(entry)
    if path is None:
        return PdbInput(fp=entry["id"], name=entry["label"],
                        error=f"PDB file for {entry['id']} not found. Expected {entry['path']}.")
    chains, err = _chains(str(path), path.stat().st_mtime)
    return PdbInput(path=str(path), chains=chains, fp=entry["id"], name=entry["label"], error=err)


# --------------------------------------------------------------------------- widgets
def _toggle(slot: str) -> None:
    other = "query" if slot == "ref" else "ref"
    st.session_state[_open_key(other)] = False      # only one chooser open at a time
    st.session_state[_open_key(slot)] = not st.session_state.get(_open_key(slot), False)


def _on_pick(slot: str, by_text: dict) -> None:
    chosen = st.session_state.get(f"analyze_chips_{slot}")
    if chosen:                                      # clicking the selected chip again keeps it
        st.session_state[_pick_key(slot)] = by_text[chosen]
    st.session_state[_open_key(slot)] = False       # close after picking


def _chips(slot: str) -> None:
    """Compact, single-select chips for every structure in this slot's list."""
    data = SLOTS[slot][1]
    by_text = {_chip_text(e): e["id"] for e in data.values()}
    current = _selected_entry(slot)
    st.pills(f"{SLOTS[slot][0]} structure", list(by_text), selection_mode="single",
             default=_chip_text(current) if current else None,
             key=f"analyze_chips_{slot}", on_change=_on_pick, args=(slot, by_text),
             label_visibility="collapsed")


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
    is_open = st.session_state.get(_open_key(slot), False)

    with st.container(border=True):
        head, action = st.columns([3, 1.2], vertical_alignment="center")
        head.markdown(f"**{title}**")
        action.button("Close" if is_open else "Choose", key=f"analyze_toggle_{slot}",
                      type="primary" if is_open else "secondary", use_container_width=True,
                      on_click=_toggle, args=(slot,))

        if is_open:
            _chips(slot)

        if entry:
            st.markdown(f"{entry['icon']}  **{entry['label']}**")
            if _details_text(entry):
                st.caption(_details_text(entry))
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