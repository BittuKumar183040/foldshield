"""Tailwind loader. Build the CSS with:
    npx @tailwindcss/cli -i tailwind.input.css -o static/tailwind.css --minify
"""
import re
from pathlib import Path

import streamlit as st

_CSS = Path(__file__).resolve().parent.parent / "static" / "tailwind.css"
_PROPERTY = re.compile(r"@property\s+(--[\w-]+)\s*\{([^}]*)\}")
_INITIAL = re.compile(r"initial-value:([^;}]+)")


def _prepare(css: str) -> str:
    """Make Tailwind's output safe for st.html.

    Streamlit sanitizes st.html with DOMPurify, which deletes the WHOLE <style>
    block if its text contains something tag-like such as  syntax:"<percentage>"
    (Tailwind emits that in its @property rules). So we drop the @property rules and
    keep their initial values as plain custom properties instead.
    """
    defaults: list[str] = []

    def _collect(m: re.Match) -> str:
        initial = _INITIAL.search(m.group(2))
        if initial:
            defaults.append(f"{m.group(1)}:{initial.group(1).strip()}")
        return ""

    css = _PROPERTY.sub(_collect, css)
    css = " ".join(css.split())
    if defaults:
        css = f"*,:before,:after,::backdrop{{{';'.join(defaults)}}}" + css
    return css


@st.cache_resource
def _read(mtime: float) -> str:
    # keyed on the file's mtime: rebuilding the CSS busts the cache automatically
    return f"<style>{_prepare(_CSS.read_text(encoding='utf-8'))}</style>"


def inject_tailwind() -> None:
    """Call once per run from app.py. Styles apply to every page."""
    if not _CSS.exists():
        st.warning(f"Tailwind CSS not found at {_CSS}. Run the build command.")
        return
    st.html(_read(_CSS.stat().st_mtime))
