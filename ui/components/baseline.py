import streamlit as st
from ui.components.cards import card_row, section, stat_card
from ui.html import fmt
from ui.theme import rmsd_color, score_color


def baseline_metrics(tm, rmsd) -> None:
    section("Coordinate baseline")
    card_row(
        stat_card("TM-score", fmt(tm, ".4f"), score_color(tm), size="xl", center=False,
                  sub="≥ 0.90 nearly identical, ≥ 0.50 same fold"),
        stat_card("RMSD (Å)", fmt(rmsd, ".3f"), rmsd_color(rmsd), size="xl", center=False,
                  sub="Lower is better, > 3.0 Å is a significant deviation"),
    )
    st.caption("Coordinate-only metrics saturate near 1.0 even when function diverges.")
