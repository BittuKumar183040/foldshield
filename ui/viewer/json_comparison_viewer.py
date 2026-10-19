"""Two 3Dmol C-alpha viewers built entirely from result summary JSON."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import streamlit as st

from ui.viewer.structure_viewer import _libs_html, _streamlit_is_dark
from visualisation.visualise_feature_extractor import TOKEN_COLORS

_ASSETS = Path(__file__).parent / "comparison_assets"


def _model_title(inputs: dict, side: str) -> str:
    # This only formats a label stored in JSON; it never opens the referenced path.
    source = str(inputs.get(f"pdb_{side}") or "").replace("\\", "/")
    model_id = source.rsplit("/", 1)[-1].rsplit(".", 1)[0] if source else side.title()
    chain = inputs.get(f"{side}_chain_id")
    return f"{side.title()} · {model_id}" + (f" · Chain {chain}" if chain else "")


def _comparison_html(config: dict, height: int) -> str:
    html = (_ASSETS / "comparison.html").read_text(encoding="utf-8")
    css = (_ASSETS / "comparison.css").read_text(encoding="utf-8")
    js = (_ASSETS / "comparison.js").read_text(encoding="utf-8")
    encoded = json.dumps(config, separators=(",", ":")).replace("</", "<\\/")
    dark = bool(config["dark"])
    return (html.replace("/*__CSS__*/", css).replace("/*__JS__*/", js)
            .replace("__CFG__", encoded).replace("__HEIGHT__", "100%")
            .replace("__BG__", "#090807" if dark else "#ffffff")
            .replace("__SCHEME__", "dark" if dark else "light")
            .replace("__WRAPCLS__", "dark" if dark else "")
            .replace("<!--__LIBS__-->", _libs_html()))


def render_json_comparison_viewer(summary: dict, *, height: int = 760) -> bool:
    """Render two independent 3Dmol C-alpha models using coordinates stored in JSON."""
    required = ("ca_coords_ref", "ca_coords_query", "tokens_ref", "tokens_query")
    if not all(key in summary for key in required):
        return False
    try:
        ref = np.asarray(summary["ca_coords_ref"], dtype=float)
        query = np.asarray(summary["ca_coords_query"], dtype=float)
        tokens_ref = [str(token) for token in summary["tokens_ref"]]
        tokens_query = [str(token) for token in summary["tokens_query"]]
    except (TypeError, ValueError):
        return False
    if (ref.ndim != 2 or query.ndim != 2 or ref.shape[1:] != (3,) or query.shape[1:] != (3,)
            or len(ref) < 2 or len(query) < 2 or len(tokens_ref) != len(ref) or len(tokens_query) != len(query)
            or not np.isfinite(ref).all() or not np.isfinite(query).all()):
        return False

    # Put each independently rendered structure around its own origin so the camera
    # synchronization behaves consistently without changing JSON coordinate data.
    ref_centered = ref - ref.mean(axis=0)
    query_centered = query - query.mean(axis=0)
    inputs = summary.get("inputs") or {}
    token_names = sorted(set(tokens_ref) | set(tokens_query))
    dark = _streamlit_is_dark()
    config = {
        "dark": dark,
        "models": [
            {"title": _model_title(inputs, "ref"), "coords": ref_centered.tolist(), "tokens": tokens_ref},
            {"title": _model_title(inputs, "query"), "coords": query_centered.tolist(), "tokens": tokens_query},
        ],
        "tokenColors": {token: (color if isinstance(color, str) else f"#{color:06x}")
                        for token, color in TOKEN_COLORS.items()},
        "tokenNames": token_names,
    }
    page = _comparison_html(config, height)
    with st.container(key="fs-json-compare-viewer"):
        st.iframe(page, height=height)
    return True
