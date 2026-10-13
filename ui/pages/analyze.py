import streamlit as st
from services import state
from services.pipeline import load_summary_upload, run_pipeline
from ui.components import AnalyzeInputs, render_inputs, empty_state
from ui.components.report import report_download
from ui.sections.results import baseline_metrics, combined_verdict, perturbation_panel, signals_panel
from ui.sections.visuals import backbone_3d, entropy_images, signal_charts
from ui.sections.log import render_log

# Width ratio of results (left) : analysis panel (right). Tweak to taste.
LAYOUT_RATIO = [3, 2]


def _handle_actions(inputs: AnalyzeInputs) -> None:
    """Turn input-panel events into a stored RunResult."""
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


def _render_results_tabs(result) -> None:
    if not result or not result.summary:
        empty_state("No results yet", "Upload a reference and a query PDB and run the pipeline, or load a saved summary.json.")
        return
    summary = result.summary
    artifacts_dir = result.artifacts_dir
    fusion = summary.get("fusion") or {}
    p2 = summary.get("phase2") or {}

    if fusion:
        combined_verdict(fusion)
    
    entropy_images(artifacts_dir)

    backbone_3d(summary)
    st.divider()
    signal_charts(summary)
    st.divider()


    if fusion.get("signal_scores") and fusion.get("per_signal"):
        signals_panel(fusion)
    if p2:
        perturbation_panel(p2)
    baseline_metrics(summary.get("tm_score"), summary.get("rmsd"))
    report_download(result.summary, artifacts_dir)

    render_log(result)


def render() -> None:
    if not state.get_result():
        _handle_actions(render_inputs())
        if state.get_result():      # a run/upload just produced a result
            st.rerun()              # switch to the results layout immediately
        return

    # page_header("Analyze", "Compare a reference and a query structure.")
    with st.expander("⚙️ Perform New Analysis", expanded=False):
        _handle_actions(render_inputs())
    _render_results_tabs(state.get_result())   # re-read: may be a new result