from functools import partial

import streamlit as st
from services import state
from services.pipeline import load_summary_upload, run_pipeline
from ui.components import AnalyzeInputs, render_inputs, empty_state
from ui.components.report import report_download
from ui.sections.results import baseline_metrics, combined_verdict, perturbation_panel, signals_panel
from ui.sections.visuals import backbone_3d, entropy_images, signal_charts
from ui.sections.log import render_log
from ui.workbench import STAGE_PCT, Tool, back_button, inject_workbench_css, panel, render_dock, render_resizer, stage, workbench

SIGNAL_CHART_HEIGHT = 230          # px, compact charts inside the side panel


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


def _go_back() -> None:
    """Drop the stored result; the next run shows the input page again."""
    state.set_result(None)


def _panel_blocks(summary: dict, fusion: dict, p2: dict) -> None:
    """Side panel content: edit / reorder / remove blocks here."""
    if fusion:
        combined_verdict(fusion)
    if fusion.get("signal_scores") and fusion.get("per_signal"):
        signals_panel(fusion)
    baseline_metrics(summary.get("tm_score"), summary.get("rmsd"))
    if p2:
        perturbation_panel(p2)
    signal_charts(summary, stacked=True, height=SIGNAL_CHART_HEIGHT)


def _render_workbench(result) -> None:
    summary = result.summary
    artifacts_dir = result.artifacts_dir
    fusion = summary.get("fusion") or {}
    p2 = summary.get("phase2") or {}

    inject_workbench_css()
    with workbench():
        left, right = st.columns([STAGE_PCT, 100 - STAGE_PCT], gap="small")

        with right, panel():
            _panel_blocks(summary, fusion, p2)

        with left, stage():
            back_button(_go_back)
            if not backbone_3d(summary, fill=True):
                empty_state("No 3D backbone", "tokens / CA coordinates were not found in this summary.")
            # ── Dock: append a Tool(...) here to add a button ─────────────────
            render_dock([
                Tool("entropy", "Entropy", partial(entropy_images, artifacts_dir),
                     icon=":material/bar_chart:", title="Entropy (reference & query)"),
                Tool("report", "Report", partial(report_download, summary, artifacts_dir),
                     icon=":material/picture_as_pdf:", title="Report preview", width="large"),
                Tool("log", "Logs", partial(render_log, result),
                     icon=":material/terminal:", title="Run log & summary"),
            ])

        # The splitter is a small same-page control; it persists its desktop width locally.
        render_resizer()


def render() -> None:
    if not state.get_result():
        _handle_actions(render_inputs())
        if state.get_result():      # a run/upload just produced a result
            st.rerun()              # switch to the workbench immediately
        return

    result = state.get_result()
    if result.summary:
        _render_workbench(result)
        return

    # A run finished without a summary: show why, with a way back to the inputs.
    st.button("Back", icon=":material/arrow_back:", on_click=_go_back)
    empty_state("No results yet", "Upload a reference and a query PDB and run the pipeline")
    render_log(result)
