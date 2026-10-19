"""Workbench shell: a 2-pane grid (3D stage | side panel) with a floating tool dock.

Desktop (> BREAKPOINT px): page never scrolls; stage ~66% | panel ~34% (panel scrolls).
Small screens:             stacked vertically, stage on top, the page scrolls.

    +------------------------------------+---------------+
    |  [Back]  STAGE (3D backbone)       |  PANEL        |
    |                                    |  (scrolls)    |
    |        [ dock: tool buttons ]      |               |
    +------------------------------------+---------------+

Add a button by appending a `Tool(...)` to the list passed to `render_dock`.
Colours come from the app theme (config.toml); nothing new is introduced.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import Callable, Literal

import streamlit as st

# ── selector constants (class names come from st.container(key=...)) ──────────
WB_KEY, STAGE_KEY, PANEL_KEY, DOCK_KEY, BACK_KEY = "fs-wb", "fs-stage", "fs-panel", "fs-dock", "fs-back"
_WB, _STAGE, _PANEL, _DOCK, _BACK = (f".st-key-{k}" for k in (WB_KEY, STAGE_KEY, PANEL_KEY, DOCK_KEY, BACK_KEY))
_MAIN = '[data-testid="stMainBlockContainer"],.stMain .block-container'
_MAIN_BLOCK = '[data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"],.block-container>[data-testid="stVerticalBlock"]'
_FRAME = '[data-testid="stFullScreenFrame"]'
_ROW = '[data-testid="stHorizontalBlock"]'
_ELEM = '[data-testid="stElementContainer"]'
_PLOT = '[data-testid="stPlotlyChart"]'
_VIEW = 'html,body,.stApp,[data-testid="stAppViewContainer"],.stMain'

STAGE_PCT = 66        # stage share of the width on desktop (rest = panel)
BREAKPOINT = 900      # px, below this the panes stack vertically
EDGE_LEFT_PX = 16     # px, gap between the window's left edge and the stage
HEADER_PX = 60        # px, Streamlit title bar; the workbench starts below it and ends flush with the bottom


@dataclass(frozen=True)
class Tool:
    """One dock button.

    mode="dialog": button opens a popup that runs `render()` (errors are shown in the popup)
    mode="action": button runs `render()` as an on_click callback
    """
    key: str
    label: str
    render: Callable[[], None]
    icon: str | None = None          # e.g. ":material/terminal:"
    mode: Literal["dialog", "action"] = "dialog"
    title: str | None = None         # popup title / tooltip (defaults to label)
    width: Literal["small", "medium", "large"] = "large"


def _theme(option: str, fallback: str) -> str:
    try:
        if st.context.theme.type == "dark":
            dark_values = {
                "backgroundColor": "#090807",
                "secondaryBackgroundColor": "#191614",
                "textColor": "#f1e9e3",
            }
            if option in dark_values:
                return dark_values[option]
    except Exception:
        pass
    return st.get_option(f"theme.{option}") or fallback


def _col(pseudo: str) -> str:
    """Selector for a direct column child of the workbench row (new + legacy test ids)."""
    return ",".join(f'{_WB} {_ROW}>[data-testid="{t}"]{pseudo}' for t in ("stColumn", "column"))


@st.cache_data(show_spinner=False)
def _workbench_css(stage_pct: int, breakpoint: int, header: int, edge_left: int, bg: str, bg2: str, fg: str) -> str:
    edge = f"1px solid color-mix(in srgb,{fg} 14%,transparent)"
    glass = f"color-mix(in srgb,{bg} 86%,transparent)"
    body_h = f"calc(100dvh - {header}px)"
    css = f"""
    {_MAIN}{{padding:0!important;max-width:100%!important}}
    {_MAIN_BLOCK}{{gap:0!important}}
    header[data-testid="stHeader"]{{background:transparent}}
    {_WB}{{gap:0!important;min-height:0!important;padding:{header}px 0 0 {edge_left}px!important;box-sizing:border-box}}
    {_STAGE}{{position:relative;overflow:hidden!important;background:{bg};gap:0!important}}
    {_STAGE} {_ELEM}:has({_PLOT}),{_STAGE} {_FRAME},{_STAGE} {_PLOT},{_STAGE} .js-plotly-plot,{_STAGE} .plot-container{{height:100%!important;min-height:0!important}}
    {_STAGE} .st-key-fs-json-compare-viewer{{height:100%!important;min-height:0!important}}
    {_STAGE} .st-key-fs-json-compare-viewer iframe{{width:100%!important;height:calc(100dvh - {header}px)!important;min-height:380px;border:0}}
    {_PANEL}{{gap:.9rem!important;padding:1rem 1.1rem 1.5rem!important;background:{bg2};border-left:{edge};overflow-x:auto}}
    {_DOCK},{_BACK}{{position:absolute;z-index:10;width:auto!important;height:auto!important;flex-direction:row!important;
      flex-wrap:wrap;align-items:center;gap:.4rem!important;padding:.35rem .5rem!important;border:{edge};
      border-radius:999px;background:{glass};backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}}
    {_DOCK}{{bottom:calc(1rem + 30px);left:50%;transform:translateX(-50%);width:max-content!important;max-width:94%;justify-content:center;
      gap:.35rem!important;padding:.4rem .5rem!important;border-radius:16px;background:{glass};box-shadow:none!important}}
    {_BACK}{{top:21px;left:22px}}
    {_DOCK} {_ELEM},{_BACK} {_ELEM}{{width:auto!important}}
    {_DOCK} button{{height:31px!important;min-height:31px!important;padding:0 .65rem!important;gap:.35rem!important;white-space:nowrap;
      font-size:.75rem!important;line-height:1!important;border:{edge}!important;border-radius:10px!important;
      background:color-mix(in srgb,{bg2} 92%,{fg} 8%)!important;color:{fg}!important;box-shadow:none!important}}
    {_DOCK} button:hover{{border-color:color-mix(in srgb,{fg} 24%,transparent)!important;transform:translateY(-1px)}}
    {_BACK}{{padding:0!important;border:0!important;border-radius:10px!important;background:transparent!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}}
    {_BACK} button{{height:31px!important;min-height:31px!important;padding:0 .65rem!important;gap:.35rem!important;white-space:nowrap;font-size:.75rem!important;line-height:1!important;border:{edge}!important;border-radius:10px!important;background:{glass}!important;color:{fg}!important;box-shadow:0 2px 4px rgba(31,74,91,.055),inset 0 1px 0 rgba(255,255,255,.7)!important}}
    {_BACK} button [data-testid="stIconMaterial"]{{font-size:15px!important}}
    @media(min-width:{breakpoint + 1}px){{
      {_VIEW}{{overflow:hidden!important;height:100dvh!important}}
      {_WB} {_ROW}{{flex-wrap:nowrap!important;gap:0!important;height:{body_h}!important;min-height:0!important;align-items:stretch!important}}
      {_col(":first-child")}{{flex:0 0 {stage_pct}%!important;width:{stage_pct}%!important;min-width:0!important}}
      {_col(":last-child")}{{flex:1 1 0!important;width:auto!important;min-width:0!important}}
      {_STAGE}{{height:{body_h}!important;flex:none!important}}
      {_PANEL}{{height:{body_h}!important;flex:none!important;overflow-y:auto!important;scrollbar-width:thin}}
    }}
    @media(max-width:{breakpoint}px){{
      {_WB} {_ROW}{{flex-direction:column!important;gap:0!important}}
      {_col("")}{{width:100%!important;flex:none!important;min-width:0!important}}
      {_STAGE}{{height:max(62dvh,380px)!important;flex:none!important}}
      {_BACK}{{top:16px;left:17px}}
      {_STAGE} .st-key-fs-json-compare-viewer iframe{{height:max(62dvh,380px)!important}}
      {_PANEL}{{height:auto!important;flex:none!important;border-left:0;border-top:{edge}}}
    }}
    """
    return " ".join(css.split())


def inject_workbench_css() -> None:
    bg = _theme("backgroundColor", "Canvas")
    css = _workbench_css(STAGE_PCT, BREAKPOINT, HEADER_PX, EDGE_LEFT_PX, bg, _theme("secondaryBackgroundColor", bg),
                         _theme("textColor", "CanvasText"))
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def workbench():
    """Outer wrapper; build `st.columns([STAGE_PCT, 100 - STAGE_PCT])` inside it."""
    return st.container(key=WB_KEY)


def stage():
    """Left pane (3D model). Call render_dock() inside it so the dock floats over the model."""
    return st.container(key=STAGE_KEY)


def panel():
    """Right pane: always visible, scrolls on desktop, flows under the stage on small screens."""
    return st.container(key=PANEL_KEY)


def back_button(on_click: Callable[[], None], label: str = "Back") -> None:
    """Floating pill at the top-left of the stage (call inside `with stage():`)."""
    with st.container(key=BACK_KEY):
        st.button(label, key="fs-back-btn", icon=":material/arrow_back:", on_click=on_click,
                  help="Back to the inputs")


def _guarded(render: Callable[[], None]) -> Callable[[], None]:
    """Run a popup body; show any error inside the popup instead of crashing the page."""
    def run() -> None:
        try:
            render()
        except Exception as e:  # noqa: BLE001 - surface everything in the popup
            st.error(f"{type(e).__name__}: {e}")
            with st.expander("Details"):
                st.code(traceback.format_exc())
    return run


def render_dock(tools: list[Tool]) -> None:
    """Floating tool dock; opens at most one popup per run."""
    to_open: Tool | None = None
    with st.container(key=DOCK_KEY):
        for t in tools:
            if t.mode == "action":
                st.button(t.label, key=f"fs-tool-{t.key}", icon=t.icon, help=None, on_click=t.render)
            elif st.button(t.label, key=f"fs-tool-{t.key}", icon=t.icon, help=None):
                to_open = t
    if to_open:
        st.dialog(to_open.title or to_open.label, width=to_open.width)(_guarded(to_open.render))()
