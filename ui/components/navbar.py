import streamlit as st
from ui import route

BRAND_NAME = "FoldShield++"
BRAND_LOGO = "https://rexcrux.com/rexcrux/foldshield.png"
LOGO_WIDTH = 36          # px
BRAND_WIDTH = 2.1        # reserve a left corner for the brand
GAP_WIDTH = 6.2          # flexible center space separates the brand from the right-side links
MENU_WIDTH = 2.1         # compact right corner for Analyze and Proteins

_CSS = """
<style>
/* Streamlit's own header used to hold the top nav. With the nav hidden it is just an empty bar
   above ours, so flatten it (the toolbar buttons are hidden by theme.py anyway). */
[data-testid="stHeader"] { display: none !important; }
[data-testid="stAppViewContainer"] [data-testid="stMainBlockContainer"] { padding-top: 3.5rem !important; }

/* sticky must sit on the wrapper Streamlit puts around the keyed container (it is a direct child of the tall page block) */
[data-testid="stLayoutWrapper"]:has(> .st-key-navbar) { position: fixed; top: 0; left: 0; z-index: 999; }

/* the bar itself: same glass look as the old header */
.st-key-navbar {
    box-sizing: border-box;
    width: 100%;
    padding: .5rem clamp(1.25rem, 4vw, 3.25rem);
    margin-bottom: 1rem;
    background: color-mix(in srgb, var(--fs-bg, #fff) 90%, transparent);
    backdrop-filter: blur(24px) saturate(135%);
    -webkit-backdrop-filter: blur(24px) saturate(135%);
    border-bottom: 1px solid var(--fs-line, rgba(128, 128, 128, .25));
    box-shadow: 0 5px 20px rgba(30, 20, 14, .06);
}
.st-key-navbar [data-testid="stHorizontalBlock"] { align-items: center; }

/* brand: bigger + bold, no "active page" pill */
.st-key-navbar_brand a, .st-key-navbar_brand a * {
    font-size: 1.25rem !important; font-weight: 700 !important; letter-spacing: -0.01em;
}
.st-key-navbar_brand a { background: transparent !important; padding-left: 0; }
.st-key-navbar_brand img { display: block; }

/* menu: right aligned, one row, pill hover / active */
.st-key-navbar_menu [data-testid="stHorizontalBlock"] { justify-content: flex-end; gap: .25rem; }
.st-key-navbar_menu a { justify-content: center; border-radius: 999px; white-space: nowrap; }
.st-key-navbar_menu a:hover { background: var(--fs-hover, rgba(128, 128, 128, .15)); }
.st-key-navbar_menu a[aria-current="page"] { background: var(--fs-primary-soft, rgba(128, 128, 128, .15)); }

/* small screens: keep brand + menu on ONE row instead of Streamlit's stacked columns */
@media (max-width: 640px) {
    [data-testid="stAppViewContainer"] [data-testid="stMainBlockContainer"] { padding-top: 5rem !important; }
    .st-key-navbar { padding: .4rem 1rem; }
    .st-key-navbar [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important}
    .st-key-navbar [data-testid="stColumn"] { min-width: 0 !important; }
    /* the empty spacer column is only needed on wide screens */
    .st-key-navbar [data-testid="stColumn"]:not(:has([data-testid="stElementContainer"], [data-testid="stLayoutWrapper"])) { display: none !important; }
    .st-key-navbar > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
    .st-key-navbar > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { flex: 0 0 auto !important; }
    .st-key-navbar_brand a, .st-key-navbar_brand a * { font-size: 1rem !important; }
    .st-key-navbar_menu a { padding: .25rem .5rem; }
    .st-key-navbar_menu [data-testid="stColumn"] { flex: 0 0 auto !important; width: auto !important; }
}
</style>
"""


def _brand(home) -> None:
    """Logo + brand name, both on the left."""
    with st.container(key="navbar_brand"):
        logo_col, name_col = st.columns([1, 15], vertical_alignment="center", gap=None)
        with logo_col:
            st.image(BRAND_LOGO, width=LOGO_WIDTH)
        with name_col:
            st.page_link(home, label=BRAND_NAME)


def _menu(items) -> None:
    """Menu links, laid out in one compact row beside the brand."""
    with st.container(key="navbar_menu"):
        cols = st.columns(len(items))
        for col, r in zip(cols, items):
            with col:
                st.page_link(
                    route._PAGES[r.key],
                    label=r.title,
                    icon=r.icon or None,
                )


def render() -> None:
    st.markdown(" ".join(_CSS.split()), unsafe_allow_html=True)

    brand_route = next((r for r in route.ROUTES if r.brand), None)
    menu_items = [r for r in route.ROUTES if not r.hidden and not r.brand]

    with st.container(key="navbar"):
        left, gap, right = st.columns(
            [BRAND_WIDTH, GAP_WIDTH, MENU_WIDTH],
            vertical_alignment="center",
        )
        with left:
            if brand_route:
                _brand(route._PAGES[brand_route.key])
        # `gap` stays empty: it is the spacer that pushes the menu right
        with right:
            _menu(menu_items)
