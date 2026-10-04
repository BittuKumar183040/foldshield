import streamlit as st
from ui.components.cards import card_row, section, stat_card
from ui.html import esc, fmt, render
from ui.theme import gap_color, score_color


def perturbation_panel(p2: dict) -> None:
    section("Perturbation classification — Phase 2")
    ssef, loc, gap = p2.get("ssef_score"), p2.get("local_topology_score"), p2.get("gap_score")
    gc = gap_color(gap)
    gap_card = f"""
    <div class="fs-card tint fs-split" style="--accent:{gc};flex-grow:2">
      <div>
        <div class="fs-label">Gap score (SSEF − local topology)</div>
        <div class="fs-value xl">{fmt(gap, "+.3f")}</div>
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
