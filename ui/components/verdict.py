import streamlit as st
from ui.components.cards import section
from ui.config import FUSION_NOTES
from ui.html import esc, fmt, render
from ui.theme import score_color


def combined_verdict(fusion: dict) -> None:
    """Headline card: the one thing a reader should see first."""
    section("Combined score — Fusion Layer v2 (Ridge CV)")
    score = fusion.get("combined_score")
    mode = fusion.get("fusion_mode", "—")
    c = score_color(score)
    render(f"""
    <div class="fs-card fs-split" style="--accent:{c};justify-content:flex-start;gap:22px;padding:18px 22px">
      <div style="text-align:center;min-width:110px">
        <div class="fs-label">Combined</div>
        <div class="fs-value xl">{fmt(score, ".4f")}</div>
        <div class="fs-sub">{esc(FUSION_NOTES.get(mode, mode))}</div>
      </div>
      <div class="fs-vr"></div>
      <div style="flex:1">
        <div class="fs-label">Verdict</div>
        <div class="fs-value sm">{esc(fusion.get("overall", "—"))}</div>
      </div>
    </div>""")
    for flag in fusion.get("flags") or []:
        st.warning(f"[FLAG] {flag}")
