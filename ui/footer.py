"""Shared, theme-native footer for the public-facing pages."""
from datetime import date

import streamlit as st

from ui.components.navbar import BRAND_LOGO
from ui.route import ROUTES, link
from ui.components.submission import SUBMISSION_URL

BRAND = "FoldShield++"
TAGLINE = ("Detects mutation impact, fold switching and conformational shifts using "
           "symbolic topology, catching what TM-score, RMSD and LDDT systematically miss.")

# Optional links in the right-hand column: (label, url). Leave empty to hide the column.
EXTERNAL_LINKS: tuple[tuple[str, str], ...] = (
    # ("Website", "https://example.com"),
    # ("Documentation", "https://example.com/docs"),
    # ("Contact", "mailto:hello@example.com"),
)


def _brand_html() -> str:
    # Keep colors inherited from Streamlit so the footer follows light and dark themes.
    return f"""
    <div style="display:flex;align-items:center;gap:.65rem;margin:.25rem 0 .75rem">
      <img src="{BRAND_LOGO}" alt="" style="height:2.25rem;width:2.25rem;object-fit:contain">
      <span style="font-size:1.2rem;font-weight:700;letter-spacing:-.01em">{BRAND}</span>
    </div>
    """


def _heading(text: str) -> None:
    st.markdown(f"**{text}**")


def _footer_css() -> str:
    background = st.get_option("theme.backgroundColor") or "Canvas"
    return f"""
    <style>
    .st-key-fs-site-footer {{
      position: relative;
      box-sizing: border-box;
      width: 100%;
      margin: 2.5rem 0 0 !important;
      padding: 2rem 0 2.5rem !important;
      background: {background};
    }}
    </style>
    """


def render_footer(*, show_model_request: bool = True) -> None:
    st.markdown(_footer_css(), unsafe_allow_html=True)
    with st.container(key="fs-site-footer"):
        has_more = show_model_request or bool(EXTERNAL_LINKS)
        ratios = [2.3, 1, 1.6] if has_more else [2.3, 1]
        columns = st.columns(ratios, gap="large", vertical_alignment="top")
        about, pages = columns[:2]
        with about:
            st.html(_brand_html())
            st.caption(TAGLINE)

        with pages:
            _heading("Explore")
            for route in ROUTES:
                if not route.hidden:
                    link(route.key, "Home" if route.default else None)

        if has_more:
            with columns[2]:
                if show_model_request:
                    _heading("Need another structure?")
                    st.caption("Request a protein model to add it to your FoldShield comparison workflow.")
                    st.link_button(
                        "Request a model",
                        SUBMISSION_URL,
                        icon=":material/add:",
                        key="footer_request_model",
                        width="stretch",
                    )
                if EXTERNAL_LINKS:
                    _heading("Links" if not show_model_request else "More")
                    for label, url in EXTERNAL_LINKS:
                        st.markdown(f"[{label}]({url})")

        left, right = st.columns([1, 1])
        left.caption(f"© {date.today().year} {BRAND}")
        right.caption("Protein structure comparison and visualization")
