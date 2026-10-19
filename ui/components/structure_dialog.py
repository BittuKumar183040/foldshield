from functools import cache
from typing import Callable, Iterable

import streamlit as st

from services import structures
from ui.components.submission import SUBMISSION_URL
from ui.viewer.structure_viewer import structure_viewer

CHIPS_PER_ROW = 3
CHIPS_PER_ROW_PREVIEW = 2
LABEL_MAX = 28
CHIP_HEIGHT = "5rem"
CHIP_TITLE_SIZE = "1.15em"   # size of the bold title (the id) in each chip
LIST_HEIGHT = 360

# --- CSS selectors (one place to change if widget keys change) ---------------
_DIALOG = '[data-testid="stDialog"]:has(.st-key-sd_dialog)'
_LIST = ".st-key-sd_list"
_LIST_WRAP = '[data-testid="stLayoutWrapper"]:has(> .st-key-sd_list)'
_VIEWER_FRAME = ".st-key-sd_viewer iframe"
_CHIP = '[class*="st-key-sd_chip_"] button'
_STYLE_HOLDER = ".stElementContainer:has(.stMarkdown style)"


@cache
def _dialog_css() -> str:
    css = f"""
        <style>
        :root {{
            --sd-vh: 100vh;
            --sd-body-h: clamp(200px, calc(var(--sd-vh) - 17rem), 640px);
            --sd-chip-h: {CHIP_HEIGHT};
            --sd-chip-title: {CHIP_TITLE_SIZE};
        }}
        @supports (height: 100dvh) {{ :root {{ --sd-vh: 100dvh; }} }}
        @media (max-width: 640px) {{
            :root {{ --sd-body-h: clamp(220px, 40vh, 420px); }}
        }}

        {_STYLE_HOLDER} {{ display: none; }}

        {_DIALOG} {{ padding-block: 1rem !important; }}
        {_DIALOG} > div {{ margin-block: auto !important; }}

        {_LIST}, {_LIST_WRAP} {{
            height: var(--sd-body-h) !important;
            max-height: var(--sd-body-h) !important;
        }}
        {_LIST} {{
            overflow: hidden auto !important;
        }}
        {_VIEWER_FRAME} {{
            height: calc(var(--sd-body-h) - 9rem) !important;
            min-height: 160px;
        }}

        {_CHIP} {{
            height: var(--sd-chip-h);
            min-height: var(--sd-chip-h);
            padding: .35rem .55rem !important;
            position: relative !important;
        }}
        {_CHIP}, {_CHIP} > div, {_CHIP} [data-testid="stMarkdownContainer"] {{
            justify-content: flex-start !important;
            text-align: left !important;
        }}
        {_CHIP} > div, {_CHIP} [data-testid="stMarkdownContainer"] {{
            min-width: 0;
            overflow: hidden;
        }}
        {_CHIP} > div {{
            margin-left: 4.6rem;
        }}
        {_CHIP} p {{
            margin: 0 !important;
            text-align: left !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        {_CHIP} strong {{
            font-size: var(--sd-chip-title) !important;
            line-height: 1.2;
        }}
        </style>
        """
    return " ".join(css.split())


def short_text(text: str | None, limit: int = LABEL_MAX) -> str:
    text = (text or "").replace("[", "(").replace("]", ")").strip() or "—"
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def details_text(entry: dict) -> str:
    """Format catalog metadata for callers that need a compact detail string."""
    return "  ·  ".join(f"{key}: {value}" for key, value in entry.get("details", {}).items())


def chip_details(entry: dict) -> str:
    details = entry.get("details", {})
    values = [str(details[key]) for key in ("Organism", "Method", "Resolution (Å)") if details.get(key)]
    return " · ".join(values)


def _preview_key(key: str) -> str:
    return f"sd_preview_{key}"


def _set_preview(key: str, pdb_id: str) -> None:
    st.session_state[_preview_key(key)] = pdb_id


def _chip(col, key: str, entry: dict, active: bool, recommended: bool = False) -> None:
    details = chip_details(entry)
    third = short_text(details) if details else "\u00a0"
    label = f"**{entry['id']}**  \n:small[{short_text(entry.get('label'))}]  \n:small[{third}]"
    chip_key = f"sd_chip_{'rec_' if recommended else ''}{key}_{entry['id']}"
    col.button(label, key=chip_key,
               type="primary" if active else "secondary", width="stretch",
               on_click=_set_preview, args=(key, entry["id"]))


def _thumbnail_css(entries: dict[str, dict], key: str) -> str:
    rules = []
    for entry in entries.values():
        pdb_id = entry["id"]
        thumbnail = entry.get("thumbnail")
        if not thumbnail:
            continue
        for recommended in (False, True):
            chip_key = f"sd_chip_{'rec_' if recommended else ''}{key}_{pdb_id}"
            selector = f".st-key-{chip_key} button"
            rules.append(
                f'{selector}::before{{content:"";position:absolute;left:.55rem;top:50%;'
                f'transform:translateY(-50%);width:4rem;height:4rem;border-radius:8px;'
                f'background-image:url("{thumbnail}");background-repeat:no-repeat;'
                f'background-position:center;background-size:contain;}}'
            )
    return "<style>" + "".join(rules) + "</style>"


def _chip_grid(key: str, entries: list[dict], per_row: int, active: str | None,
               recommended_ids: set[str] | None = None) -> None:
    recommended_ids = recommended_ids or set()
    for i in range(0, len(entries), per_row):
        cols = st.columns(per_row)
        for col, entry in zip(cols, entries[i:i + per_row]):
            _chip(col, key, entry, entry["id"] == active, entry["id"] in recommended_ids)




def _organism_groups(entries: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = {}
    for item in entries:
        organism = str(item.get("details", {}).get("Organism") or "Organism not specified").strip()
        groups.setdefault(organism, []).append(item)
    return sorted(groups.items(), key=lambda group: group[0].casefold())


def _grouped_chips(key: str, entries: list[dict], per_row: int, active: str | None,
                   recommended_ids: set[str] | None = None) -> None:
    groups = _organism_groups(entries)
    for organism, items in groups:
        with st.expander(f"{organism}  ·  {len(items)}", expanded=True):
            _chip_grid(key, items, per_row, active, recommended_ids)


def _split(entries: dict[str, dict], exclude: str | None, recommended: Iterable[str]):
    pool = {i: e for i, e in entries.items() if i != exclude}
    first = [pool[i] for i in dict.fromkeys(r for r in recommended if r) if i in pool]
    shown = {e["id"] for e in first}
    return first, [e for e in pool.values() if e["id"] not in shown], pool


def _body(key: str, entries: dict, exclude, recommended, recommended_label, on_choose) -> None:
    first, rest, pool = _split(entries, exclude, recommended)
    preview_id = st.session_state.get(_preview_key(key))
    entry = pool.get(preview_id)

    st.markdown(_dialog_css() + _thumbnail_css(entries, key), unsafe_allow_html=True)
    with st.container(key="sd_dialog"):
        left, right = st.columns([1.15, 1], gap="medium") if entry else (st.container(), None)
        per_row = CHIPS_PER_ROW_PREVIEW if entry else CHIPS_PER_ROW
        with left:
            with st.container(key="sd_list", border=False, height=LIST_HEIGHT):
                if first:
                    st.caption(recommended_label or "Recommended")
                    _grouped_chips(key, first, per_row, preview_id, {item["id"] for item in first})
                if rest:
                    st.caption("Other structures" if first else "Choose a structure")
                    _grouped_chips(key, rest, per_row, preview_id)
                st.link_button(
                    "Request Model",
                    SUBMISSION_URL,
                    icon=":material/add:",
                    key=f"sd_request_model_{key}",
                    width="stretch",
                )
        if right is not None:
            with right:
                model_panel(entry)

        _, confirm = st.columns([3, 1])
        if confirm.button("Choose", type="primary", key=f"sd_confirm_{key}", disabled=entry is None,
                          width="stretch", help=None if entry else "Click a structure to preview it first."):
            on_choose(entry["id"])
            st.rerun()

def model_panel(entry: dict, key: str = "sd_viewer") -> None:
    st.markdown(f"{entry.get('icon', '')}  **{entry['id']}**  \n:small[{short_text(entry.get('label'), 60)}]")
    with st.container(key=key):
        structure_viewer(**structures.viewer_args(entry), fill=True, height=LIST_HEIGHT, minimal=True)

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
