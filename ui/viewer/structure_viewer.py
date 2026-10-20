# 3D Mol based previewer for protein structures. Used in the Proteins page and in the Analyzer page.
# Have different views options controlled by the user, including style, color, rotation, and more. The viewer is implemented as a Streamlit component that renders an HTML page with embedded JavaScript and CSS.

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import streamlit as st

_ASSETS = Path(__file__).parent / "viewer_assets"
_STATIC = Path(__file__).parent / "static"
_LIBS = ("3Dmol-min.js", "lucide.min.js")

_STYLES = ("cartoon", "surface", "cartoon+sticks", "sticks", "ballstick", "spheres", "lines")
_COLORS = ("spectrum", "chain", "ss", "residue", "bfactor", "element")


@lru_cache(maxsize=1)
def _libs_html() -> str:
    blocks = []
    for name in _LIBS:
        code = (_STATIC / name).read_text(encoding="utf-8")
        code = re.sub(r"//# sourceMappingURL=\S+\s*$", "", code)
        code = code.replace("</script", "<\\/script")
        blocks.append(f"<script>\n{code}\n</script>")
    return "\n".join(blocks)


def _build_html(cfg: dict, box_height: str) -> str:
    html = (_ASSETS / "viewer.html").read_text(encoding="utf-8")
    css = (_ASSETS / "viewer.css").read_text(encoding="utf-8")
    js = (_ASSETS / "viewer.js").read_text(encoding="utf-8")
    cfg_json = json.dumps(cfg).replace("</", "<\\/") 
    dark = bool(cfg.get("dark"))
    # theme + minimal are applied in the HTML itself, so the very first paint is already right
    wrap_cls = " ".join(c for c, on in (("dark", dark), ("minimal", cfg.get("minimal"))) if on)
    html = (html.replace("/*__CSS__*/", css).replace("/*__JS__*/", js)
                .replace("__CFG__", cfg_json).replace("__HEIGHT__", box_height)
                .replace("__BG__", "#090807" if dark else "#ffffff")
                .replace("__SCHEME__", "dark" if dark else "light")
                .replace("__WRAPCLS__", wrap_cls))
    return html.replace("<!--__LIBS__-->", _libs_html())


def _streamlit_is_dark() -> bool:
    """FoldShield's embedded structure viewers always use the light palette."""
    return False

def structure_viewer(*, pdb_id: str | None = None, pdb_text: str | None = None, height: int = 620,
                     fill: bool = False, auto_rotate: bool | None = None, minimal: bool = False,
                     style: str = "cartoon", color_by: str = "spectrum", dark: bool | None = None,
                     fmt: str = "pdb") -> None:
    """Render a structure in the 3Dmol viewer.

    minimal=True gives a compact view with no side panels. Fullscreen switches to the full toolbar
    and panels; leaving fullscreen returns to the compact view. Auto-rotation defaults on in
    minimal mode and off otherwise. Set auto_rotate to override that default.

    The viewer uses FoldShield's fixed light palette for consistency across devices.
    """
    if not pdb_text and not pdb_id:
        st.info("No structure available for this entry.")
        return
    dark = False
    cfg = {
        "pdbId": str(pdb_id) if (pdb_id and not pdb_text) else None,
        "pdbText": pdb_text or None,
        "fmt": fmt,
        "autoRotate": bool(minimal) if auto_rotate is None else bool(auto_rotate),
        "minimal": bool(minimal),
        "style": style if style in _STYLES else "cartoon",
        "colorBy": color_by if color_by in _COLORS else "spectrum",
        "dark": bool(dark),
    }
    box_height = "100vh" if fill else f"{height - 10}px"
    html = _build_html(cfg, box_height)
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)          # new API (st.components.v1.html is being removed)
    else:                                       # older Streamlit versions
        import streamlit.components.v1 as components
        components.html(html, height=height)
