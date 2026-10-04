"""Generic building blocks. Every other component is composed from these."""
import streamlit as st
from ui.html import esc, render


def badge(text: str) -> str:
    return f'<span class="fs-badge">{esc(text)}</span>' if text else ""


def stat_card(label, value, color, *, sub="", badge_text="", size="",
              center=True, tint=False, grow=1) -> str:
    """Return HTML for one metric card (compose with card_row / card_grid)."""
    cls = "fs-card" + (" center" if center else "") + (" tint" if tint else "")
    sub_html = f'<div class="fs-sub">{esc(sub)}</div>' if sub else ""
    return (
        f'<div class="{cls}" style="--accent:{color};flex-grow:{grow}">'
        f'<div class="fs-label">{esc(label)}{badge(badge_text)}</div>'
        f'<div class="fs-value {size}">{esc(value)}</div>{sub_html}</div>'
    )


def card_row(*cards: str) -> None:
    render(f'<div class="fs-row">{"".join(cards)}</div>')


def card_grid(cards) -> None:
    render(f'<div class="fs-grid">{"".join(cards)}</div>')


def section(title: str, caption: str | None = None) -> None:
    st.markdown(f"#### {title}")
    if caption:
        st.caption(caption)


def page_header() -> None:
    st.title("FoldShield++ — Protein Similarity Demo")


def empty_state(title: str, hint: str) -> None:
    render(f'<div class="fs-empty"><b>{esc(title)}</b><span>{esc(hint)}</span></div>')
