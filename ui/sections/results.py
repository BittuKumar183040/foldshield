"""Results tab. Reorder / remove blocks by editing the list in render_results()."""
import streamlit as st
from ui.components import (baseline_metrics, combined_verdict, empty_state,
                           perturbation_panel, report_download, signals_panel)


def render_results(result) -> None:
    if not result or not result.summary:
        empty_state("No results yet",
                    "Upload a reference and a query PDB and run the pipeline, or load a saved summary.json.")
        return

    summary = result.summary
    fusion = summary.get("fusion") or {}
    p2 = summary.get("phase2") or {}

    blocks = []
    if fusion:
        blocks.append(lambda: combined_verdict(fusion))
    if fusion.get("signal_scores") and fusion.get("per_signal"):
        blocks.append(lambda: signals_panel(fusion))
    if p2:
        blocks.append(lambda: perturbation_panel(p2))
    blocks.append(lambda: baseline_metrics(summary.get("tm_score"), summary.get("rmsd")))
    blocks.append(lambda: report_download(summary, result.artifacts_dir))

    for i, block in enumerate(blocks):
        if i:
            st.divider()
        block()
