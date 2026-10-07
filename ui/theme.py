"""Design tokens + the one stylesheet. Change colours / thresholds / look HERE only."""
import streamlit as st

# Status palette
GOOD, WARN, BAD, MUTED = "#2a9d8f", "#f4a261", "#e76f51", "#999999"
BRAND = "#2E75B6"

# Similarity bands (score >= HI is good, >= LO is borderline)
HI, LO = 0.66, 0.33


def score_color(value) -> str:
    """Colour for a 0..1 similarity score (higher is better)."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return MUTED
    return GOOD if f >= HI else WARN if f >= LO else BAD


def rmsd_color(value, scale: float = 5.0) -> str:
    """Colour for RMSD in Å (lower is better; `scale` Å maps to a score of 0)."""
    try:
        return score_color(1.0 - float(value) / scale)
    except (TypeError, ValueError):
        return MUTED


def gap_color(gap) -> str:
    """Colour for |SSEF - local topology| gap."""
    if gap is None:
        return MUTED
    a = abs(gap)
    return GOOD if a < 0.15 else WARN if a < 0.36 else BAD


# Translucent greys so every component works in light AND dark mode.
_CSS = """
<style>
.fs-row, .fs-grid { margin: 4px 0 14px; }
.fs-row  { display: flex; gap: 14px; flex-wrap: wrap; }
.fs-grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); }
.fs-split { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.fs-vr { width: 1px; align-self: stretch; background: rgba(128,128,128,.3); }

.fs-card { flex: 1 1 160px; padding: 14px 16px; border-radius: 8px;
           border: 1px solid rgba(128,128,128,.28); border-top: 4px solid var(--accent, #999);
           background: rgba(128,128,128,.05); }
.fs-card.center { text-align: center; }
.fs-card.tint   { background: color-mix(in srgb, var(--accent) 9%, transparent); border-color: var(--accent); }

.fs-label { font-size: 13px; font-weight: 500; opacity: .75; margin-bottom: 6px; line-height: 1.3; }
.fs-value { font-size: 30px; font-weight: 700; line-height: 1; color: var(--accent, inherit); }
.fs-value.xl { font-size: 38px; }
.fs-value.sm { font-size: 17px; line-height: 1.3; }
.fs-sub   { font-size: 12px; opacity: .65; margin-top: 6px; }

.fs-badge { display: inline-block; margin-left: 6px; padding: 1px 6px; border-radius: 4px;
            font-size: 10px; font-weight: 600; background: rgba(46,117,182,.16); color: #2E75B6; }
.fs-pill  { display: inline-block; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 700;
            background: color-mix(in srgb, var(--accent) 16%, transparent); color: var(--accent); }

.fs-tablewrap { overflow-x: auto; border: 1px solid rgba(128,128,128,.28); border-radius: 8px; margin: 8px 0 14px; }
.fs-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.fs-table th { padding: 10px 12px; text-align: left; font-size: 12px; background: rgba(128,128,128,.10); }
.fs-table td { padding: 10px 12px; border-top: 1px solid rgba(128,128,128,.2); }
.fs-table .nowrap { white-space: nowrap; font-weight: 500; }
.fs-table .num { text-align: center; font-size: 15px; font-weight: 700; }
.fs-table .mid { text-align: center; opacity: .75; }

.fs-bar { height: 10px; border-radius: 8px; background: rgba(128,128,128,.2); }
.fs-bar > div { height: 100%; border-radius: 8px; }

.fs-empty { padding: 36px 20px; text-align: center; border: 1px dashed rgba(128,128,128,.4);
            border-radius: 8px; margin-top: 8px; }
.fs-empty b { display: block; font-size: 16px; margin-bottom: 6px; }
.fs-empty span { opacity: .7; font-size: 14px; }
.stMainBlockContainer { padding-top: 50px; padding-bottom: 50px; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
