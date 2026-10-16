import base64
import html
import json
from pathlib import Path

import streamlit as st

from services import state
from services.pipeline import RunResult
from static.samples import SAMPLES
from ui.components import card_row, page_header, section, stat_card
from ui.components.submission import submission_card
from ui.html import fmt
from ui.route import go
from ui.theme import score_color
from ui.footer import render_footer

ROOT = Path(__file__).resolve().parents[2]   # project root (this file is ui/pages/home.py)
COLUMNS = 4                                  # cards per row; Streamlit stacks them on narrow screens
THUMB_HEIGHT = 150                           # px, same for every card so rows line up


# --------------------------------------------------------------------------- data helpers
@st.cache_data(show_spinner=False)
def _load_summary(path: str, mtime: float) -> dict | None:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


@st.cache_data(show_spinner=False)
def _thumb_uri(path: str, mtime: float) -> str:
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def _sample_files(sample: dict) -> dict:
    """Paths of everything inside a sample's result folder."""
    folder = ROOT / sample["path"]
    ref, query = sample["id"].removeprefix("ca_").split("_vs_")
    return {
        "folder": folder,
        "thumbnail": folder / "thumbnail.png",
        "summary": folder / "summary.json",
        "ref_pdb": folder / f"{ref}.pdb",
        "query_pdb": folder / f"{query}.pdb",
    }


def _open_in_analyzer(summary: dict, folder: Path) -> None:
    state.set_result(RunResult(summary=summary, outdir=str(folder)))
    go("analyze")


# --------------------------------------------------------------------------- card
def _card_html(sample: dict, thumb_uri: str | None, fusion: dict) -> str:
    e = html.escape
    # Inline styles only (no <style> block, no Tailwind), so they work anywhere st.html does.
    if thumb_uri:
        thumb = f'<img src="{thumb_uri}" alt="" style="width:100%;height:100%;object-fit:contain">'
    else:
        thumb = '<span style="font-size:12px;opacity:.6">Structure preview unavailable</span>'

    pills = "".join(
        f'<span style="font-size:11px;padding:3px 9px;border-radius:999px;'
        f'background:rgba(128,128,128,.14);border:1px solid rgba(128,128,128,.16);white-space:nowrap">{e(t)}</span>'
        for t in sample.get("tags", [])
    )

    score = fusion.get("combined_score")
    if score is not None:
        verdict = e(str(fusion.get("overall", "")))
        footer = (
            '<div style="display:flex;justify-content:space-between;align-items:baseline;font-size:13px;gap:8px">'
            '<span style="opacity:.7">Combined score</span>'
            f'<b style="color:{score_color(score)};font-size:16px">{fmt(score, ".4f")}</b></div>'
            f'<div style="font-size:12px;opacity:.6;min-height:1.2em">{verdict}</div>'
        )
    else:
        footer = '<div style="font-size:12px;opacity:.5">No summary.json found yet</div>'

    return f"""
    <div style="display:flex;flex-direction:column;gap:10px">
      <div style="height:{THUMB_HEIGHT}px;border-radius:12px;background:rgba(128,128,128,.07);
                  border:1px solid rgba(128,128,128,.16);box-shadow:inset 0 1px 5px rgba(128,128,128,.10);
                  display:flex;align-items:center;justify-content:center;overflow:hidden">{thumb}</div>
      <div title="{e(sample['title'])}" style="font-size:15px;font-weight:650;white-space:nowrap;
                  overflow:hidden;text-overflow:ellipsis">{e(sample['title'])}</div>
      <div style="display:flex;flex-wrap:wrap;gap:5px;min-height:30px;max-height:52px;overflow:hidden;align-content:flex-start">{pills}</div>
      <p title="{e(sample['desc'])}" style="margin:0;font-size:13px;line-height:1.5;opacity:.78;
                  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;
                  height:calc(1.5em * 3)">{e(sample['desc'])}</p>
      <div style="height:44px">{footer}</div>
    </div>
    """


def _sample_card(key: str, sample: dict) -> None:
    files = _sample_files(sample)
    thumb_uri = None
    if files["thumbnail"].exists():
        thumb_uri = _thumb_uri(str(files["thumbnail"]), files["thumbnail"].stat().st_mtime)
    summary = None
    if files["summary"].exists():
        summary = _load_summary(str(files["summary"]), files["summary"].stat().st_mtime)
    fusion = (summary or {}).get("fusion") or {}

    with st.container(border=True):
        st.html(_card_html(sample, thumb_uri, fusion))
        if st.button("Open in Analyzer", key=f"sample_{key}", width="stretch",
                     disabled=summary is None):
            _open_in_analyzer(summary, files["folder"])


def _sample_grid() -> None:
    items = list(SAMPLES.items())
    for i in range(0, len(items), COLUMNS):
        cols = st.columns(COLUMNS)
        for col, (key, sample) in zip(cols, items[i:i + COLUMNS]):
            with col:
                _sample_card(key, sample)


# --------------------------------------------------------------------------- page
def render() -> None:
    page_header(
        "Protein Similarity Platform",
        "Compare protein structures, explore curated examples, and inspect each model in 3D.",
    )

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader(":material/compare_arrows: Compare structures")
        st.write("Choose a reference and query PDB, then run the FoldShield analysis.")
        st.caption("Best for testing a mutation, a different state, or a related fold.")
        if st.button("Start an analysis", type="primary", key="home_analyze"):
            go("analyze")
    with right, st.container(border=True):
        st.subheader(":material/biotech: Browse proteins")
        st.write("Search the PDB collection and open any available structure in 3D.")
        st.caption("Review structure metadata and inspect chains interactively.")
        if st.button("Explore proteins", key="home_proteins"):
            go("proteins")

    submission_card(
        title="Bring your own protein model",
        description="Can’t find the structure you need? Request an upload to have your protein compared with FoldShield.",
        key="home_request_upload",
        button_label="Request a comparison",
    )

    st.divider()
    section("Sample comparisons", f"{len(SAMPLES)} ready-to-explore pairs. Open any result to continue in the analyzer.")
    _sample_grid()
    render_footer()
