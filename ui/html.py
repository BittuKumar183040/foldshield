"""Tiny helpers for emitting HTML from Streamlit safely."""
import html as _html
import streamlit as st


def esc(value) -> str:
    """HTML-escape anything (None -> empty string)."""
    return _html.escape("" if value is None else str(value))


def fmt(value, spec: str = ".3f", dash: str = "—") -> str:
    """Format a number, or return a dash when it is missing / not numeric."""
    try:
        return format(float(value), spec)
    except (TypeError, ValueError):
        return dash


def render(markup: str) -> None:
    """Render HTML. Per-line indentation is stripped because Markdown treats
    4+ leading spaces as a code block."""
    st.markdown("".join(line.strip() for line in markup.splitlines()),
                unsafe_allow_html=True)
