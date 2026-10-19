"""Visuals tab: entropy images, 3D backbone, signal charts."""
import os

import streamlit as st
from ui.charts import signal_bar_fig, signal_radar_fig
from ui.components import section
from ui.viewer.json_comparison_viewer import render_json_comparison_viewer


def entropy_images(outdir: str) -> None:
    print(f"entropy_images: outdir={outdir}")
    items = [("entropy_ref.png", "Entropy (Reference)"), ("entropy_query.png", "Entropy (Query)")]
    found = [(os.path.join(outdir, f), cap) for f, cap in items if outdir and os.path.exists(os.path.join(outdir, f))]
    if not found:
        section("Entropy")
        return
    for col, (path, caption) in zip(st.columns(len(found)), found):
        col.image(path, caption=caption, width="stretch")


def backbone_3d(summary: dict, fill: bool = False) -> bool:
    """Render the JSON C-alpha backbones in two linked 3Dmol canvases."""
    if not fill:
        section("UL-DSL tokenized backbone (3D)")
    return render_json_comparison_viewer(summary, height=760 if fill else 640)


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
        st.plotly_chart(bar, width="stretch")
    with right:
        section("Signal profile")
        st.plotly_chart(radar, width="stretch")
