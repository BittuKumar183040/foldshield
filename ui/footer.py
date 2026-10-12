"""Site footer, shown at the bottom of every page.

Add it once, in app.py, right after the router runs:

    build_navigation().run()      # runs the current page
    render_footer()               # then the footer, below it

It reads the pages from ui/route.py, so a new Route shows up in the footer automatically
(routes with hidden=True are skipped). Edit the constants below to change the text and links.
"""
from datetime import date

import streamlit as st

from ui.route import BRAND_ICON, ROUTES, link

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
    # inline styles only, so it looks right in light and dark themes
    return f"""
    <div style="display:flex;align-items:center;gap:.6rem">
      <img src="{BRAND_ICON}" alt="" style="height:2rem;width:2rem;object-fit:contain">
      <span style="font-size:1.15rem;font-weight:700;letter-spacing:-.01em">{BRAND}</span>
    </div>
    """


def _heading(text: str) -> None:
    st.markdown(f"**{text}**")


def render_footer() -> None:
    st.divider()

    about, pages, more = st.columns([2.2, 1, 1])        # the last column stays empty without EXTERNAL_LINKS
    with about:
        st.html(_brand_html())
        st.caption(TAGLINE)

    with pages:
        _heading("Pages")
        for r in ROUTES:
            if not r.hidden:
                link(r.key, "Home" if r.default else None)

    if EXTERNAL_LINKS:
        with more:
            _heading("Links")
            for label, url in EXTERNAL_LINKS:
                st.markdown(f"[{label}]({url})")

    st.caption(f"© {date.today().year} {BRAND}")
