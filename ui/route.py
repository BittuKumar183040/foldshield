import importlib
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class Route:
    key: str
    title: str
    icon: str
    module: str
    default: bool = False
    hidden: bool = False
    brand: bool = False


ROUTES = (
    Route("home", "FoldShield++", "", "ui.pages.home", default=True, brand=True),
    Route("analyze", "Analyze", ":material/science:", "ui.pages.analyze"),
    Route("proteins", "Proteins", ":material/biotech:", "ui.pages.proteins"),
)

_PAGES: dict = {}  # key -> st.Page (refreshed on every run)
_PARAMS = "_route_params"


def _make_page(route: Route):
    # Pages are imported lazily, so pages can import this module without a cycle.
    render = importlib.import_module(route.module).render
    kwargs = {"title": route.title, "default": route.default}
    if route.icon:
        kwargs["icon"] = route.icon
    if not route.default:
        kwargs["url_path"] = route.key
    return st.Page(render, **kwargs)


def build_navigation():
    """Register pages and hide Streamlit's own nav; navbar.py draws it."""
    for route in ROUTES:
        _PAGES[route.key] = _make_page(route)
    pages = [_PAGES[route.key] for route in ROUTES]
    return st.navigation(pages, position="hidden")


def go(key: str, **params) -> None:
    """Jump to a page, optionally passing parameters (read them with param())."""
    st.session_state[_PARAMS] = params
    st.switch_page(_PAGES[key])


def link(key: str, label: str | None = None) -> None:
    """Create a clickable link to a page."""
    route = next(route for route in ROUTES if route.key == key)
    st.page_link(_PAGES[key], label=label or route.title, icon=route.icon or None)


def param(name: str, default=None):
    """Return a URL query parameter, falling back to a value passed via go()."""
    return st.query_params.get(name) or st.session_state.get(_PARAMS, {}).get(name, default)


def set_param(name: str, value) -> None:
    """Write a parameter into the URL so the current view can be shared or refreshed."""
    st.query_params[name] = str(value)
