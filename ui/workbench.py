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

_RESIZER_HTML = """
<script>
(() => {
  const rowSelector = '.st-key-fs-wb [data-testid="stHorizontalBlock"]';
  const storageKey = 'foldshield-workbench-stage-width';

  function attach() {
    const row = document.querySelector(rowSelector);
    const columns = row && row.querySelectorAll(':scope > [data-testid="stColumn"], :scope > [data-testid="column"]');
    if (!row || !columns || columns.length < 2) return;

    row.classList.add('fs-resizable-row');
    let handle = row.querySelector(':scope > .fs-panel-resizer');
    if (!handle) {
      handle = document.createElement('div');
      handle.className = 'fs-panel-resizer';
      handle.setAttribute('role', 'separator');
      handle.setAttribute('aria-orientation', 'vertical');
      handle.setAttribute('aria-label', 'Resize visualization and results panel');
      handle.setAttribute('tabindex', '0');
      handle.setAttribute('aria-valuemin', '38');
      handle.setAttribute('aria-valuemax', '78');
      handle.title = 'Drag to resize the results panel';
      row.appendChild(handle);
    }
    if (handle.dataset.ready === 'true') return;
    handle.dataset.ready = 'true';

    const clamp = value => {
      const width = row.getBoundingClientRect().width;
      const min = Math.max(38, Math.min(58, 360 / width * 100));
      const max = Math.min(78, (width - 320) / width * 100);
      return Math.max(min, Math.min(max, value));
    };
    const apply = value => {
      const pct = clamp(value);
      row.style.setProperty('--fs-stage-pct', pct + '%');
      handle.setAttribute('aria-valuenow', String(Math.round(pct)));
    };

    let initial = 66;
    try {
      const stored = Number(localStorage.getItem(storageKey));
      if (Number.isFinite(stored) && stored > 0) initial = stored;
    } catch (_) { /* Storage can be unavailable in private browsing. */ }
    if (window.matchMedia('(min-width: 901px)').matches) apply(initial);
    else row.style.setProperty('--fs-stage-pct', initial + '%');
    window.addEventListener('resize', () => {
      if (!window.matchMedia('(min-width: 901px)').matches) return;
      const current = parseFloat(row.style.getPropertyValue('--fs-stage-pct')) || initial;
      apply(current);
    });

    let dragging = false;
    handle.addEventListener('pointerdown', event => {
      if (window.matchMedia('(max-width: 900px)').matches) return;
      dragging = true;
      handle.setPointerCapture(event.pointerId);
      document.body.classList.add('fs-resizing-workbench');
      event.preventDefault();
    });
    handle.addEventListener('pointermove', event => {
      if (!dragging) return;
      const rect = row.getBoundingClientRect();
      apply((event.clientX - rect.left) / rect.width * 100);
    });
    const finish = () => {
      if (!dragging) return;
      dragging = false;
      document.body.classList.remove('fs-resizing-workbench');
      try { localStorage.setItem(storageKey, row.style.getPropertyValue('--fs-stage-pct').replace('%', '')); }
      catch (_) { /* Keep the current-session resize if storage is unavailable. */ }
    };
    handle.addEventListener('pointerup', finish);
    handle.addEventListener('pointercancel', finish);
    handle.addEventListener('keydown', event => {
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
      event.preventDefault();
      const current = parseFloat(row.style.getPropertyValue('--fs-stage-pct')) || 66;
      apply(current + (event.key === 'ArrowLeft' ? -2 : 2));
      try { localStorage.setItem(storageKey, row.style.getPropertyValue('--fs-stage-pct').replace('%', '')); }
      catch (_) { /* Ignore unavailable storage. */ }
    });
  }

  attach();
  if (window.__fsWorkbenchObserver) window.__fsWorkbenchObserver.disconnect();
  window.__fsWorkbenchObserver = new MutationObserver(attach);
  window.__fsWorkbenchObserver.observe(document.body, { childList: true, subtree: true });
})();
</script>
"""


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
    light_values = {
        "backgroundColor": "#fdfcfb",
        "secondaryBackgroundColor": "#ffffff",
        "textColor": "#2b211b",
    }
    return light_values.get(option, st.get_option(f"theme.{option}") or fallback)


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
    {_PANEL}{{--fs-panel-line:color-mix(in srgb,{fg} 11%,transparent);gap:.7rem!important;
      padding:1.2rem 1.25rem 1.6rem!important;background:color-mix(in srgb,{bg2} 86%,transparent);
      border-left:1px solid var(--fs-panel-line);backdrop-filter:blur(22px) saturate(125%);
      -webkit-backdrop-filter:blur(22px) saturate(125%);overflow-x:hidden}}
    {_PANEL} h4{{display:flex;align-items:center;gap:.55rem;margin:.3rem 0 .15rem!important;
      font-size:.94rem!important;font-weight:720!important;letter-spacing:-.015em!important}}
    {_PANEL} h4:before{{content:"";width:3px;height:1rem;flex:0 0 3px;border-radius:3px;
      background:color-mix(in srgb,{fg} 24%,transparent)}}
    {_PANEL} h4 + [data-testid="stCaptionContainer"]{{margin-top:-.18rem;margin-bottom:.1rem}}
    {_PANEL} [data-testid="stCaptionContainer"]{{font-size:.76rem;line-height:1.45}}
    {_PANEL} .fs-row{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem;margin:.2rem 0 .65rem}}
    {_PANEL} .fs-row:has(.fs-pill) .fs-card:last-child{{grid-column:1 / -1}}
    {_PANEL} .fs-grid{{grid-template-columns:repeat(2,minmax(0,1fr));gap:.65rem;margin:.2rem 0 .65rem}}
    {_PANEL} .fs-card{{min-width:0;padding:13px 14px;border-radius:14px;border-top-width:2px;
      box-shadow:0 4px 14px color-mix(in srgb,{fg} 5%,transparent),inset 0 1px 0 color-mix(in srgb,{fg} 8%,transparent)}}
    {_PANEL} .fs-label{{font-size:.74rem;line-height:1.35;margin-bottom:.4rem}}
    {_PANEL} .fs-value{{font-size:1.65rem;line-height:1.05}}
    {_PANEL} .fs-value.xl{{font-size:1.9rem}}
    {_PANEL} .fs-sub{{font-size:.68rem;line-height:1.4;margin-top:.4rem}}
    {_PANEL} .fs-badge{{font-size:.58rem;padding:2px 6px}}
    {_PANEL} .fs-combined-card{{display:flex;align-items:center;gap:1rem;padding:16px 17px;
      background:linear-gradient(125deg,color-mix(in srgb,var(--accent) 10%,{bg2}),{bg2})}}
    {_PANEL} .fs-combined-score{{min-width:106px;text-align:center}}
    {_PANEL} .fs-combined-score .fs-value{{font-size:2.25rem}}
    {_PANEL} .fs-combined-card .fs-vr{{min-height:52px;background:var(--fs-panel-line)}}
    {_PANEL} .fs-combined-verdict{{min-width:0;flex:1;padding:.2rem .15rem}}
    {_PANEL} .fs-eyebrow{{font-size:.61rem;font-weight:750;letter-spacing:.09em;opacity:.65;margin-bottom:.4rem}}
    {_PANEL} .fs-verdict-text{{font-size:.92rem;font-weight:700;line-height:1.35;color:{fg}}}
    {_PANEL} .fs-tablewrap{{border-radius:12px;margin:.3rem 0 .6rem}}
    {_PANEL} .fs-table{{table-layout:fixed;font-size:.7rem}}
    {_PANEL} .fs-table th{{padding:8px 7px;font-size:.63rem;letter-spacing:.025em}}
    {_PANEL} .fs-table td{{padding:8px 7px;line-height:1.4;overflow-wrap:anywhere}}
    {_PANEL} .fs-table th:nth-child(1){{width:31%}}
    {_PANEL} .fs-table th:nth-child(2){{width:14%;text-align:center}}
    {_PANEL} .fs-table th:nth-child(3){{width:40%}}
    {_PANEL} .fs-table th:nth-child(4){{width:15%;text-align:center}}
    {_PANEL} .fs-table .nowrap{{white-space:normal;font-weight:600}}
    {_PANEL} .fs-table .num{{font-size:.75rem}}
    {_PANEL} .fs-table tbody tr{{transition:background .15s}}
    {_PANEL} .fs-table tbody tr:hover{{background:color-mix(in srgb,{fg} 4%,transparent)}}
    {_PANEL} [data-testid="stAlert"]{{padding:.55rem .72rem;margin:.25rem 0;border-radius:11px!important}}
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
      {_WB} {_ROW}{{position:relative!important;flex-wrap:nowrap!important;gap:0!important;height:{body_h}!important;min-height:0!important;align-items:stretch!important}}
      {_col(":first-child")}{{flex:0 0 var(--fs-stage-pct,{stage_pct}%)!important;width:var(--fs-stage-pct,{stage_pct}%)!important;min-width:0!important}}
      {_col(":last-child")}{{flex:1 1 0!important;width:auto!important;min-width:0!important}}
      {_STAGE}{{height:{body_h}!important;flex:none!important}}
      {_PANEL}{{height:{body_h}!important;flex:none!important;overflow-y:auto!important;scrollbar-width:thin}}
      .fs-panel-resizer{{position:absolute;z-index:24;top:0;bottom:0;left:var(--fs-stage-pct,{stage_pct}%);
        width:16px;transform:translateX(-50%);display:flex;align-items:center;justify-content:center;
        cursor:col-resize;touch-action:none;outline:none}}
      .fs-panel-resizer:after{{content:"";width:3px;height:46px;border-radius:999px;
        background:color-mix(in srgb,{fg} 24%,transparent);transition:height .16s,background .16s}}
      .fs-panel-resizer:hover:after,.fs-panel-resizer:focus-visible:after{{height:68px;background:{fg}}}
      body.fs-resizing-workbench,body.fs-resizing-workbench *{{cursor:col-resize!important;user-select:none!important}}
    }}
    @media(max-width:{breakpoint}px){{
      {_WB} {_ROW}{{flex-direction:column!important;gap:0!important}}
      {_col("")}{{width:100%!important;flex:none!important;min-width:0!important}}
      {_STAGE}{{height:max(62dvh,380px)!important;flex:none!important}}
      {_BACK}{{top:16px;left:17px}}
      {_STAGE} .st-key-fs-json-compare-viewer iframe{{height:max(62dvh,380px)!important}}
      {_PANEL}{{height:auto!important;flex:none!important;border-left:0;border-top:{edge}}}
      .fs-panel-resizer{{display:none!important}}
    }}
    @media(max-width:1100px){{
      {_PANEL}{{padding:1rem!important}}
      {_PANEL} .fs-row{{gap:.5rem}}
      {_PANEL} .fs-card{{padding:11px 12px}}
    }}
    @media(max-width:560px){{
      {_PANEL} .fs-row{{grid-template-columns:1fr}}
      {_PANEL} .fs-grid{{grid-template-columns:1fr}}
      {_PANEL} .fs-table{{min-width:430px}}
      {_PANEL} .fs-combined-card{{gap:.65rem;padding:13px 12px}}
      {_PANEL} .fs-combined-score{{min-width:92px}}
      {_PANEL} .fs-combined-score .fs-value{{font-size:1.9rem}}
      {_PANEL} .fs-verdict-text{{font-size:.84rem}}
    }}
    """
    return " ".join(css.split())


def inject_workbench_css() -> None:
    bg = _theme("backgroundColor", "Canvas")
    css = _workbench_css(STAGE_PCT, BREAKPOINT, HEADER_PX, EDGE_LEFT_PX, bg, _theme("secondaryBackgroundColor", bg),
                         _theme("textColor", "CanvasText"))
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_resizer() -> None:
    """Add the accessible desktop splitter; it is hidden when panes stack on mobile."""
    st.html(_RESIZER_HTML, width="content", unsafe_allow_javascript=True)


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
