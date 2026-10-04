from dataclasses import dataclass
from typing import Any

import streamlit as st
from services.inputs import PdbInput, resolve_pdb


@dataclass
class SidebarInputs:
    ref: PdbInput
    query: PdbInput
    ref_chain: str
    query_chain: str
    mode: str
    keep_hetatm: bool
    summary_upload: Any
    run_clicked: bool


def _chain_picker(label: str, slot: str, pdb: PdbInput) -> str:
    key = f"chain_{slot}_{pdb.fp}"          # new file -> fresh widget state
    if not pdb.ready:
        st.selectbox(label, ["—"], disabled=True, key=key)
        return "A"
    if pdb.chains:
        return st.selectbox(label, pdb.chains, key=key)
    return st.text_input(label, value="A", key=key)


def render_sidebar() -> SidebarInputs:
    with st.sidebar:
        st.header("Inputs")

        st.markdown("**Structures**")
        ref = resolve_pdb("ref", st.file_uploader("Reference PDB", type=["pdb"]))
        query = resolve_pdb("query", st.file_uploader("Query PDB", type=["pdb"]))
        for pdb in (ref, query):
            if pdb.error:
                st.warning(pdb.error)

        st.markdown("**Chains**")
        c1, c2 = st.columns(2)
        with c1:
            ref_chain = _chain_picker("Reference", "ref", ref)
        with c2:
            query_chain = _chain_picker("Query", "query", query)

        with st.expander("Options", expanded=True):
            mode = st.radio("Coordinate mode", ["ca", "sequence"], index=0, horizontal=True)
            keep_hetatm = st.checkbox("Keep HETATM", value=False)

        ready = ref.ready and query.ready
        run = st.button("Run pipeline", type="primary", use_container_width=True,
                        disabled=not ready,
                        help=None if ready else "Upload both PDB files first.")

        st.divider()
        with st.expander("Load a saved run"):
            summary_upload = st.file_uploader("summary.json", type=["json"])

    return SidebarInputs(ref, query, ref_chain, query_chain, mode, keep_hetatm, summary_upload, run)
