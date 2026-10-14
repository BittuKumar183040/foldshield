"""Visuals tab: entropy images, 3D backbone, signal charts."""
import os

import numpy as np
import streamlit as st
from ui.charts import signal_bar_fig, signal_radar_fig
from ui.components import section
from visualisation.visualise_feature_extractor import plot_dual_pdb_token_backbones_plotly_separate


def entropy_images(outdir: str) -> None:
    print(f"entropy_images: outdir={outdir}")
    items = [("entropy_ref.png", "Entropy (Reference)"), ("entropy_query.png", "Entropy (Query)")]
    found = [(os.path.join(outdir, f), cap) for f, cap in items if outdir and os.path.exists(os.path.join(outdir, f))]
    if not found:
        section("Entropy")
        return
    for col, (path, caption) in zip(st.columns(len(found)), found):
        col.image(path, caption=caption, use_container_width=True)


def backbone_3d(summary: dict, fill: bool = False) -> bool:
    """Draw the 3D backbone. Returns False when the summary has no 3D data.

    fill=True stretches the chart to its container (workbench stage) and keeps the
    camera across reruns (e.g. when a popup opens); no section header is drawn.
    """
    keys = ("tokens_ref", "tokens_query", "ca_coords_ref", "ca_coords_query")
    if not all(k in summary for k in keys):
        return False
    if not fill:
        section("UL-DSL tokenized backbone (3D)")
    fig = plot_dual_pdb_token_backbones_plotly_separate(
        np.array(summary["ca_coords_ref"]), summary["tokens_ref"],
        np.array(summary["ca_coords_query"]), summary["tokens_query"])
    if not fill:
        st.plotly_chart(fig, use_container_width=True)
        return True
    fig.update_layout(autosize=True, uirevision="fs-stage")
    try:
        st.plotly_chart(fig, width="stretch", height="stretch")
    except TypeError:       # older Streamlit: no height="stretch"
        fig.update_layout(height=700)
        st.plotly_chart(fig, use_container_width=True)
    return True


def signal_charts(summary: dict, stacked: bool = False, height: int | None = None) -> None:
    """stacked=True puts bar over radar (narrow panel); height sets both chart heights in px."""
    fusion = summary.get("fusion") or {}
    scores = fusion.get("signal_scores") or {}
    if not scores:
        st.info("Phase 2 signal scores not found in summary.")
        return
    combined = float(summary.get("combined_similarity") or fusion.get("combined_score") or 0)
    bar, radar = signal_bar_fig(scores, combined), signal_radar_fig(scores)
    if height:
        bar.update_layout(height=height)
        radar.update_layout(height=height)
    left, right = (st.container(), st.container()) if stacked else st.columns(2)
    with left:
        section("Signal scores")
        st.plotly_chart(bar, use_container_width=True)
    with right:
        section("Signal profile")
        st.plotly_chart(radar, use_container_width=True)