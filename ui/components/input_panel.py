"""Inputs for the Analyze page, laid out on the page itself (no sidebar).

Reference and Query each get a card. The card's "Choose" button opens a grid of chips,
one per structure in static/samples.py (PDBs). A chip shows:  logo, bold id, and the label
in small text underneath. Clicking a chip selects it and closes the grid.

The other card's selection shapes the list:
  * the structure already chosen on the other side is left out
  * its `recommendation` ids are moved to the top under a "Recommended" heading
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from services.inputs import PdbInput, detect_chains
from static.samples import PDBs
from ui.components.cards import section

ROOT = Path(__file__).resolve().parents[2]          # project root

CHIPS_PER_ROW = 3
LIST_HEIGHT = 330                                   # px; the chip grid scrolls inside this
LABEL_MAX = 28                                      # safety cut in Python; CSS adds the "…" when it still does not fit
CHIP_HEIGHT = "3.4rem"                              # every chip is exactly two lines tall

# slot -> (title, data)
SLOTS = {"ref": ("Reference", PDBs), "query": ("Query", PDBs)}

# Chips are st.buttons; their `key` becomes a CSS class (st-key-analyze_chip_...), which is how
# we restyle only these buttons: left-aligned, fixed height, each of the two lines clipped with "…".
_CHIP_CSS = """
<style>
[class*="st-key-analyze_chip_"] button {
    height: %(h)s; min-height: %(h)s; padding: .3rem .65rem;
    justify-content: flex-start !important; text-align: left !important;
}
[class*="st-key-analyze_chip_"] button > div,
[class*="st-key-analyze_chip_"] button [data-testid="stMarkdownContainer"] {
    justify-content: flex-start !important; text-align: left !important;
    min-width: 0; overflow: hidden;
}
[class*="st-key-analyze_chip_"] button p {
    margin: 0 !important; text-align: left !important; line-height: 1.3;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
</style>
""" % {"h": CHIP_HEIGHT}


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


def _resolve(entry: dict | None) -> PdbInput:
    if entry is None:
        return PdbInput()
    path = _find_pdb(entry)
    if path is None:
        return PdbInput(fp=entry["id"], name=entry["id"],
                        error=f"PDB file for {entry['id']} not found. Expected {entry['path']}.")
    chains, err = _chains(str(path), path.stat().st_mtime)
    return PdbInput(path=str(path), chains=chains, fp=entry["id"], name=entry["id"], error=err)


def _candidates(slot: str) -> tuple[list[dict], list[dict], dict | None]:
    """(recommended, others, the other side's selection) for this slot's chip list."""
    data = SLOTS[slot][1]
    other = _selected_entry(_other(slot))
    pool = [e for e in data.values() if not (other and e["id"] == other["id"])]
    wanted = [r for r in (other or {}).get("recommendation", []) if r]
    by_id = {e["id"]: e for e in pool}
    recommended = [by_id[r] for r in dict.fromkeys(wanted) if r in by_id]     # keeps their order
    rest = [e for e in pool if e["id"] not in {r["id"] for r in recommended}]
    return recommended, rest, other


# --------------------------------------------------------------------------- chips
def _toggle(slot: str) -> None:
    st.session_state[_open_key(_other(slot))] = False      # only one chooser open at a time
    st.session_state[_open_key(slot)] = not st.session_state.get(_open_key(slot), False)


def _pick(slot: str, pdb_id: str) -> None:
    st.session_state[_pick_key(slot)] = pdb_id
    st.session_state[_open_key(slot)] = False              # close after picking


def _short(text: str, limit: int = LABEL_MAX) -> str:
    text = (text or "").replace("[", "(").replace("]", ")").strip() or "—"
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _chip(col, slot: str, entry: dict, selected: bool) -> None:
    # logo on the left; line 1 = bold id, line 2 = small label (both clipped to one line by the CSS)
    label = f"**{entry['id']}**  \n:small[{_short(entry.get('label'))}]"
    tip = " · ".join(x for x in (entry.get("label"), entry.get("details", {}).get("Protein")) if x)
    col.button(label, key=f"analyze_chip_{slot}_{entry['id']}", icon=entry.get("icon"),
               type="primary" if selected else "secondary", use_container_width=True,
               help=tip or None, on_click=_pick, args=(slot, entry["id"]))


def _chip_grid(slot: str, entries: list[dict]) -> None:
    current = st.session_state.get(_pick_key(slot))
    for i in range(0, len(entries), CHIPS_PER_ROW):
        cols = st.columns(CHIPS_PER_ROW)
        for col, entry in zip(cols, entries[i:i + CHIPS_PER_ROW]):
            _chip(col, slot, entry, entry["id"] == current)


def _chooser(slot: str) -> None:
    recommended, rest, other = _candidates(slot)
    with st.container(height=LIST_HEIGHT, border=False):
        if recommended:
            st.caption(f"⭐ Recommended for {other['id']}")
            _chip_grid(slot, recommended)
        if rest:
            st.caption("Other structures" if recommended else "Choose a structure")
            _chip_grid(slot, rest)


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
    is_open = st.session_state.get(_open_key(slot), False)

    with st.container(border=True):
        head, action = st.columns([3, 1.2], vertical_alignment="center")
        head.markdown(f"**{title}**")
        action.button("Close" if is_open else "Choose", key=f"analyze_toggle_{slot}",
                      type="primary" if is_open else "secondary", use_container_width=True,
                      on_click=_toggle, args=(slot,))

        if is_open:
            _chooser(slot)

        if entry:
            st.markdown(f"{entry['icon']}  **{entry['id']}**  \n:small[{_short(entry.get('label'), 60)}]")
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
    st.markdown(" ".join(_CHIP_CSS.split()), unsafe_allow_html=True)   # same method as ui/theme.py's inject_css
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