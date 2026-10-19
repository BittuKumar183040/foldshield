"""Results tab. Reorder / remove blocks by editing the list in render_results()."""
import streamlit as st
from ui.components.signals import signal_cards, signal_table
from ui.components.cards import card_row, section, stat_card
from ui.config import FUSION_NOTES
from ui.html import esc, fmt, render
from ui.theme import score_color, rmsd_color, gap_color


def baseline_metrics(tm, rmsd) -> None:
    section("Coordinate baseline")
    card_row(
        stat_card("TM-score", fmt(tm, ".4f"), score_color(tm), size="xl", center=False,
                  sub="≥ 0.90 nearly identical, ≥ 0.50 same fold"),
        stat_card("RMSD (Å)", fmt(rmsd, ".3f"), rmsd_color(rmsd), size="xl", center=False,
                  sub="Lower is better, > 3.0 Å is a significant deviation"),
    )
    st.caption("Coordinate-only metrics saturate near 1.0 even when function diverges.")



def combined_verdict(fusion: dict) -> None:
    """Headline card: the one thing a reader should see first."""
    section("Combined score", "Fusion Layer v2 · " + FUSION_NOTES.get(fusion.get("fusion_mode"), "Fusion score"))
    score = fusion.get("combined_score")
    c = score_color(score)
    render(f"""
    <div class="fs-card fs-combined-card" style="--accent:{c}">
      <div class="fs-combined-score">
        <div class="fs-label">Similarity score</div>
        <div class="fs-value xl">{fmt(score, ".4f")}</div>
      </div>
      <div class="fs-vr"></div>
      <div class="fs-combined-verdict">
        <div class="fs-eyebrow">OVERALL VERDICT</div>
        <div class="fs-verdict-text">{esc(fusion.get("overall", "—"))}</div>
      </div>
    </div>""")
    for flag in fusion.get("flags") or []:
        st.warning(f"[FLAG] {flag}")



def signals_panel(fusion: dict) -> None:
    section("FoldShield++ signals", "Signal scores and their contribution to the combined result")
    per_signal = fusion.get("per_signal") or {}
    scores = fusion.get("signal_scores") or {}
    weights = fusion.get("weights_used") or {}
    signal_cards(per_signal, scores, weights)
    signal_table(per_signal, scores, weights)


def perturbation_panel(p2: dict) -> None:
    section("Perturbation", "Phase 2 structural change classification")
    ssef, loc, gap = p2.get("ssef_score"), p2.get("local_topology_score"), p2.get("gap_score")
    gc = gap_color(gap)
    gap_card = f"""
    <div class="fs-card tint fs-split" style="--accent:{gc};flex-grow:2">
      <div>
        <div class="fs-label">Gap score</div>
        <div class="fs-value xl">{fmt(gap, "+.3f")}</div>
        <div class="fs-sub">SSEF − local topology</div>
      </div>
      <div style="text-align:right">
        <div class="fs-sub" style="margin:0 0 6px">Perturbation class</div>
        <span class="fs-pill">{esc(p2.get("perturbation_class", "—"))}</span>
      </div>
    </div>"""
    card_row(
        stat_card("SSEF score", fmt(ssef), score_color(ssef)),
        stat_card("Local topology", fmt(loc), score_color(loc)),
        gap_card,
    )
    if p2.get("local_topology_unreliable"):
        st.warning("Local topology flagged unreliable — large length mismatch.")
    if p2.get("ssef_note"):
        st.warning(f"SSEF: {p2['ssef_note']}")
