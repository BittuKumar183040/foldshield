# app.py — entry point only: page setup, wiring, tabs. Layout lives in ui/, logic in services/.
import streamlit as st

from services import state
from services.pipeline import load_summary_upload, run_pipeline
from ui.components import SidebarInputs, page_header, render_sidebar
from ui.sections import render_log, render_results, render_visuals
from ui.theme import inject_css

st.set_page_config(page_title="FoldShield++", page_icon="🧬", layout="wide")
inject_css()
page_header()

def handle_actions(inputs: SidebarInputs) -> None:
    """Turn sidebar events into a stored RunResult."""
    if inputs.summary_upload and state.is_new_upload(inputs.summary_upload):
        loaded = load_summary_upload(inputs.summary_upload)
        if loaded.summary:
            state.set_result(loaded)
        else:
            st.error(loaded.error)

    if inputs.run_clicked:
        with st.spinner("Running FoldShield pipeline…"):
            result = run_pipeline(
                inputs.ref.path, inputs.query.path,
                mode=inputs.mode, keep_hetatm=inputs.keep_hetatm,
                ref_chain=inputs.ref_chain, query_chain=inputs.query_chain)
        state.set_result(result)
        if result.summary is None:
            st.error("Run finished but no summary was produced. Check the Log tab.")
        else:
            st.success("Run finished. Summary loaded.")

handle_actions(render_sidebar())

result = state.get_result()
tab_results, tab_visuals, tab_log = st.tabs(["Results", "Visuals", "Log"])
with tab_results:
    render_results(result)
with tab_visuals:
    render_visuals(result)
with tab_log:
    render_log(result)
