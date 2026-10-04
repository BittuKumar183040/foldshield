"""Visuals tab: entropy images, 3D backbone, signal charts."""
import os

import numpy as np
import streamlit as st
from ui.charts import signal_bar_fig, signal_radar_fig
from ui.components import empty_state, section
from visualisation.visualise_feature_extractor import plot_dual_pdb_token_backbones_plotly_separate


def _entropy_images(outdir: str) -> None:
    items = [("entropy_ref.png", "Entropy (Reference)"), ("entropy_query.png", "Entropy (Query)")]
    found = [(os.path.join(outdir, f), cap) for f, cap in items if outdir and os.path.exists(os.path.join(outdir, f))]
    if not found:
        return
    section("Entropy")
    for col, (path, caption) in zip(st.columns(len(found)), found):
        col.image(path, caption=caption, use_container_width=True)


def _backbone_3d(summary: dict) -> None:
    keys = ("tokens_ref", "tokens_query", "ca_coords_ref", "ca_coords_query")
    if not all(k in summary for k in keys):
        return
    section("UL-DSL tokenized backbone (3D)")
    fig = plot_dual_pdb_token_backbones_plotly_separate(
        np.array(summary["ca_coords_ref"]), summary["tokens_ref"],
        np.array(summary["ca_coords_query"]), summary["tokens_query"])
    st.plotly_chart(fig, use_container_width=True)


def _signal_charts(summary: dict) -> None:
    fusion = summary.get("fusion") or {}
    scores = fusion.get("signal_scores") or {}
    if not scores:
        st.info("Phase 2 signal scores not found in summary.")
        return
    combined = float(summary.get("combined_similarity") or fusion.get("combined_score") or 0)
    left, right = st.columns(2)
    with left:
        section("Signal scores")
        st.plotly_chart(signal_bar_fig(scores, combined), use_container_width=True)
    with right:
        section("Signal profile")
        st.plotly_chart(signal_radar_fig(scores), use_container_width=True)


def render_visuals(result) -> None:
    if not result or not result.summary:
        empty_state("Nothing to show yet", "Run the pipeline or load a summary.json to see images and charts.")
        return
    _entropy_images(result.artifacts_dir)
    _backbone_3d(result.summary)
    st.divider()
    _signal_charts(result.summary)
