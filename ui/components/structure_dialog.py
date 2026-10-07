from typing import Callable, Iterable

import streamlit as st

from services import structures
from ui.components.viewer import structure_viewer

CHIPS_PER_ROW = 4
CHIPS_PER_ROW_PREVIEW = 2
LABEL_MAX = 28
CHIP_HEIGHT = "4.4rem"
LIST_HEIGHT = 360
VIEWER_HEIGHT = LIST_HEIGHT - 140

_CSS = """
<style>
:root { --sd-vh: 100vh; --sd-body-h: clamp(200px, calc(var(--sd-vh) - 17rem), 640px); }
@supports (height: 100dvh) { :root { --sd-vh: 100dvh; } }
@media (max-width: 640px) { :root { --sd-body-h: clamp(220px, 40vh, 420px); } }

[data-testid="stDialog"]:has(.st-key-sd_dialog) {
    padding-top: 1rem !important; padding-bottom: 1rem !important;
}
[data-testid="stDialog"]:has(.st-key-sd_dialog) > div {
    margin-top: auto !important; margin-bottom: auto !important;
}

.st-key-sd_list,
[data-testid="stLayoutWrapper"]:has(> .st-key-sd_list) {
    height: var(--sd-body-h) !important; max-height: var(--sd-body-h) !important;
}
.st-key-sd_list { overflow-y: auto !important; overflow-x: hidden !important; padding-right: .25rem; }
.st-key-sd_viewer iframe { height: calc(var(--sd-body-h) - 9rem) !important; min-height: 160px; }

[class*="st-key-sd_chip_"] button {
    height: __H__; min-height: __H__; padding: .3rem .65rem;
    justify-content: flex-start !important; text-align: left !important;
}
[class*="st-key-sd_chip_"] button > div,
[class*="st-key-sd_chip_"] button [data-testid="stMarkdownContainer"] {
    justify-content: flex-start !important; text-align: left !important;
    min-width: 0; overflow: hidden;
}
[class*="st-key-sd_chip_"] button p {
    margin: 0 !important; text-align: left !important; line-height: 1.3;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
</style>
""".replace("__H__", CHIP_HEIGHT)

def short_text(text: str | None, limit: int = LABEL_MAX) -> str:
    text = (text or "").replace("[", "(").replace("]", ")").strip() or "—"
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"

def details_text(entry: dict) -> str:
    return "  ·  ".join(f"{k}: {v}" for k, v in entry.get("details", {}).items())

def chip_details(entry: dict) -> str:
    label = entry.get("label")
    values = [str(v) for v in entry.get("details", {}).values() if v and v != label]
    return " · ".join(values)

def _preview_key(key: str) -> str:
    return f"sd_preview_{key}"

def _set_preview(key: str, pdb_id: str) -> None:
    st.session_state[_preview_key(key)] = pdb_id

def _chip(col, key: str, entry: dict, active: bool) -> None:
    third = short_text(chip_details(entry)) if chip_details(entry) else "\u00a0"
    label = f"**{entry['id']}**  \n:small[{short_text(entry.get('label'))}]  \n:small[{third}]"
    tip = " · ".join(x for x in (entry.get("label"), entry.get("details", {}).get("Protein")) if x)
    col.button(label, key=f"sd_chip_{key}_{entry['id']}", icon=entry.get("icon"),
               type="primary" if active else "secondary", width="stretch",
               help=tip or None, on_click=_set_preview, args=(key, entry["id"]))

def _chip_grid(key: str, entries: list[dict], per_row: int, active: str | None) -> None:
    for i in range(0, len(entries), per_row):
        cols = st.columns(per_row)
        for col, entry in zip(cols, entries[i:i + per_row]):
            _chip(col, key, entry, entry["id"] == active)

def _model_panel(entry: dict) -> None:
    st.markdown(f"{entry.get('icon', '')}  **{entry['id']}**  \n:small[{short_text(entry.get('label'), 60)}]")
    with st.container(key="sd_viewer"):
        structure_viewer(**structures.viewer_args(entry), fill=True, height=VIEWER_HEIGHT)

def _split(entries: dict[str, dict], exclude: str | None, recommended: Iterable[str]):
    pool = {i: e for i, e in entries.items() if i != exclude}
    first = [pool[i] for i in dict.fromkeys(r for r in recommended if r) if i in pool]
    shown = {e["id"] for e in first}
    return first, [e for e in pool.values() if e["id"] not in shown], pool

def _body(key: str, entries: dict, exclude, recommended, recommended_label, on_choose) -> None:
    first, rest, pool = _split(entries, exclude, recommended)
    preview_id = st.session_state.get(_preview_key(key))
    entry = pool.get(preview_id)

    st.html(_CSS)
    with st.container(key="sd_dialog"):
        
        left, right = st.columns([1.15, 1], gap="medium") if entry else (st.container(), None)
        per_row = CHIPS_PER_ROW_PREVIEW if entry else CHIPS_PER_ROW
        with left:
            with st.container(key="sd_list", border=False, height=LIST_HEIGHT):
                if first:
                    st.caption(recommended_label or "Recommended")
                    _chip_grid(key, first, per_row, preview_id)
                if rest:
                    st.caption("Other structures" if first else "Choose a structure")
                    _chip_grid(key, rest, per_row, preview_id)
        if right is not None:
            with right:
                _model_panel(entry)

        _, confirm = st.columns([3, 1])
        if confirm.button("Choose", type="primary", key=f"sd_confirm_{key}", disabled=entry is None,
                          width="stretch", help=None if entry else "Click a structure to preview it first."):
            on_choose(entry["id"])
            st.rerun()

def open_structure_dialog(*, key: str, title: str, entries: dict[str, dict],
                          exclude: str | None = None, recommended: Iterable[str] = (),
                          recommended_label: str | None = None,
                          on_choose: Callable[[str], None]) -> None:
    st.session_state[_preview_key(key)] = None
    recommended = list(recommended)

    @st.dialog(title, width="large")
    def _dialog() -> None:
        _body(key, entries, exclude, recommended, recommended_label, on_choose)

    _dialog()