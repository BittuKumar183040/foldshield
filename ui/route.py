"""Routing: the single place that knows which pages exist.

Add a page:
  1. create ui/pages/<name>.py that exposes render()
  2. add one Route(...) to ROUTES below
Navigate from any page with  route.go("key", **params)  or  route.link("key").
"""
import importlib
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class Route:
    key: str                  # also the URL path: /<key>
    title: str
    icon: str
    module: str               # dotted path of a module exposing render()
    default: bool = False     # served at "/"
    hidden: bool = False      # reachable by link/URL, not shown in the nav bar


ROUTES = (
    Route("home",     "Home",     "🏠", "ui.pages.home", default=True),
    Route("analyze",  "Analyze",  "🧪", "ui.pages.analyze"),
    Route("proteins", "Proteins", "🧬", "ui.pages.proteins"),
    Route("protein",  "Protein",  "🧬", "ui.pages.protein", hidden=True),
)

_PAGES: dict = {}             # key -> st.Page (refreshed on every run)
_PARAMS = "_route_params"

def _make_page(r: Route):
    # Pages are imported lazily, so pages can import this module without a cycle.
    render = importlib.import_module(r.module).render
    kwargs = dict(title=r.title, icon=r.icon, default=r.default)
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
    st.page_link(_PAGES[key], label=label or r.title, icon=r.icon)


def param(name: str, default=None):
    """URL query param first (shareable link), else the value passed via go()."""
    return st.query_params.get(name) or st.session_state.get(_PARAMS, {}).get(name, default)


def set_param(name: str, value) -> None:
    """Write a param into the URL so the current view can be shared / refreshed."""
    st.query_params[name] = str(value)
