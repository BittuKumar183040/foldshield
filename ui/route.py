"""Routing: the single place that knows which pages exist.

Add a page:
  1. create ui/pages/<name>.py that exposes render()
  2. add one Route(...) to ROUTES below
Navigate from any page with  route.go("key", **params)  or  route.link("key").
"""
import importlib
from dataclasses import dataclass

import streamlit as st

# Brand image shown in front of the brand route's nav label. st.Page(icon=...) only accepts an
# emoji or a Material icon, so the image is added with CSS instead (see _brand_css).
BRAND_ICON = "https://rexcrux.com/rexcrux/foldshield.png"


@dataclass(frozen=True)
class Route:
    key: str                  # also the URL path: /<key>
    title: str
    icon: str
    module: str               # dotted path of a module exposing render()
    default: bool = False     # served at "/"
    hidden: bool = False      # reachable by link/URL, not shown in the nav bar
    brand: bool = False       # styled as the app brand: custom image + bigger, bold label


ROUTES = (
    Route("home",     "FoldShield++", "", "ui.pages.home", default=True, brand=True),
    Route("analyze",  "Analyze",  "🧪", "ui.pages.analyze"),
    Route("proteins", "Proteins", "🧬", "ui.pages.proteins")
)

_PAGES: dict = {}             # key -> st.Page (refreshed on every run)
_PARAMS = "_route_params"

# The default page's nav link points at the site root, so its href ends with "/"
# (every other page is "/<key>"). That is how the brand link is picked out.
_BRAND_LINK = '[data-testid="stTopNavLink"][href$="/"]'


def _brand_css() -> str:
    css = f"""
        <style>
        {_BRAND_LINK} {{ display: inline-flex !important; align-items: center; gap: .5rem; }}
        {_BRAND_LINK}::before {{
            content: ""; flex: none; width: 1.9rem; height: 1.9rem;
            background: url("{BRAND_ICON}") center / contain no-repeat;
        }}
        {_BRAND_LINK} * {{
            font-size: 1rem !important; font-weight: 600 !important; letter-spacing: -0.01em;
        }}
        </style>
        """
    return " ".join(css.split())          # one line, so Markdown cannot split the block

def _make_page(r: Route):
    # Pages are imported lazily, so pages can import this module without a cycle.
    render = importlib.import_module(r.module).render
    kwargs = dict(title=r.title, default=r.default)
    if r.icon:                              # leave it out entirely for "no icon" (icon="" is rejected by some versions)
        kwargs["icon"] = r.icon
    if not r.default:
        kwargs["url_path"] = r.key
    if r.hidden:
        kwargs["visibility"] = "hidden"
    try:
        return st.Page(render, **kwargs)
    except TypeError:                       # older Streamlit: no "visibility"
        kwargs.pop("visibility", None)
        return st.Page(render, **kwargs)


def build_navigation():
    """Create the pages + nav bar. Call once from app.py, then .run() the result."""
    for r in ROUTES:
        _PAGES[r.key] = _make_page(r)
    if any(r.brand for r in ROUTES):
        st.markdown(_brand_css(), unsafe_allow_html=True)   # same method as ui/theme.py's inject_css
    pages = [_PAGES[r.key] for r in ROUTES]
    try:
        return st.navigation(pages, position="top")
    except TypeError:                       # older Streamlit: sidebar nav only
        return st.navigation(pages)


def go(key: str, **params) -> None:
    """Jump to a page, optionally passing parameters (read them with param())."""
    st.session_state[_PARAMS] = params
    st.switch_page(_PAGES[key])


def link(key: str, label: str | None = None) -> None:
    """Clickable link to a page."""
    r = next(r for r in ROUTES if r.key == key)
    st.page_link(_PAGES[key], label=label or r.title, icon=r.icon or None)


def param(name: str, default=None):
    """URL query param first (shareable link), else the value passed via go()."""
    return st.query_params.get(name) or st.session_state.get(_PARAMS, {}).get(name, default)


def set_param(name: str, value) -> None:
    """Write a param into the URL so the current view can be shared / refreshed."""
    st.query_params[name] = str(value)