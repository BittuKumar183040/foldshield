"""Shared FoldShield palette and globally fixed light application styles."""
import streamlit as st

GOOD, WARN, BAD, MUTED = "#2a9d8f", "#f4a261", "#e76f51", "#8794a3"
BRAND = "#d89267"
HI, LO = 0.66, 0.33


def score_color(value) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return MUTED
    return GOOD if f >= HI else WARN if f >= LO else BAD


def rmsd_color(value, scale: float = 5.0) -> str:
    try:
        return score_color(1.0 - float(value) / scale)
    except (TypeError, ValueError):
        return MUTED


def gap_color(gap) -> str:
    if gap is None:
        return MUTED
    a = abs(gap)
    return GOOD if a < 0.15 else WARN if a < 0.36 else BAD


_PALETTES = {
    "light": """
      color-scheme:light;
      --fs-bg:#fdfcfb;--fs-bg-image:radial-gradient(ellipse at 12% 0%,rgba(216,146,103,.075),transparent 36%),radial-gradient(ellipse at 94% 8%,rgba(179,126,96,.045),transparent 34%),linear-gradient(180deg,#fff 0%,#faf8f6 100%);
      --fs-surface:rgba(255,255,255,.58);--fs-surface-strong:rgba(255,255,255,.78);--fs-surface-soft:rgba(255,252,249,.48);
      --fs-ink:#2b211b;--fs-muted:#74645a;--fs-line:rgba(92,62,43,.15);--fs-line-strong:rgba(92,62,43,.24);
      --fs-primary:#d89267;--fs-primary-dark:#844b30;--fs-primary-solid:#95522f;--fs-primary-soft:rgba(216,146,103,.14);--fs-primary-ink:#fff;
      --fs-header:rgba(255,255,255,.58);--fs-nav:rgba(255,255,255,.54);--fs-input:rgba(255,255,255,.72);
      --fs-shadow:0 14px 36px rgba(78,50,33,.075),0 2px 8px rgba(78,50,33,.035);--fs-shadow-soft:0 7px 20px rgba(78,50,33,.055);
      --fs-inset:rgba(255,255,255,.78);--fs-hover:rgba(216,146,103,.075);--fs-table-head:rgba(216,146,103,.075);
    """,
    "dark": """
      color-scheme:dark;
      --fs-bg:#090807;--fs-bg-image:radial-gradient(ellipse at 14% 0%,rgba(216,146,103,.12),transparent 35%),radial-gradient(ellipse at 96% 8%,rgba(147,77,42,.09),transparent 31%),linear-gradient(180deg,#12100e 0%,#090807 100%);
      --fs-surface:rgba(25,22,20,.88);--fs-surface-strong:#211d1a;--fs-surface-soft:rgba(35,29,25,.88);
      --fs-ink:#f1e9e3;--fs-muted:#b6a69b;--fs-line:rgba(216,146,103,.19);--fs-line-strong:rgba(216,146,103,.32);
      --fs-primary:#d89267;--fs-primary-dark:#edb28f;--fs-primary-solid:#95522f;--fs-primary-soft:rgba(216,146,103,.17);--fs-primary-ink:#fff;
      --fs-header:rgba(12,10,9,.76);--fs-nav:rgba(22,19,17,.84);--fs-input:rgba(28,24,21,.96);
      --fs-shadow:0 14px 36px rgba(0,0,0,.24),0 2px 8px rgba(0,0,0,.15);--fs-shadow-soft:0 7px 20px rgba(0,0,0,.2);
      --fs-inset:rgba(255,255,255,.035);--fs-hover:rgba(216,146,103,.12);--fs-table-head:rgba(216,146,103,.12);
    """,
}

_CSS = """
<style>
:root{__PALETTE__--fs-line-rgb:92,62,43;--fs-copper:#d89267}
html,body,[data-testid="stAppViewContainer"]{background:var(--fs-bg)!important;color:var(--fs-ink)!important}
[data-testid="stAppViewContainer"]{background-image:var(--fs-bg-image)!important;background-attachment:fixed!important}
[data-testid="stHeader"]{background:var(--fs-header)!important;backdrop-filter:blur(24px) saturate(135%)!important;-webkit-backdrop-filter:blur(24px) saturate(135%)!important;border-bottom:1px solid var(--fs-line);box-shadow:0 5px 20px rgba(30,20,14,.06)}
[data-testid="stDeployButton"],button[data-testid="stMainMenu"],#MainMenu,[data-testid="stDecoration"]{display:none!important}
[data-testid="stMainBlockContainer"]{padding-top:2.2rem!important;padding-bottom:0!important}
[data-testid="stVerticalBlock"]{gap:1rem}
[data-testid="stNavigation"]{display:flex!important;visibility:visible!important;opacity:1!important;background:var(--fs-nav)!important;border:1px solid var(--fs-line);border-bottom-color:var(--fs-line-strong);box-shadow:0 5px 22px rgba(30,20,14,.055),inset 0 1px 0 var(--fs-inset);backdrop-filter:blur(26px) saturate(145%)!important;-webkit-backdrop-filter:blur(26px) saturate(145%)!important}
[data-testid="stTopNavLink"]{border-radius:999px!important;color:var(--fs-muted)!important;transition:background .18s,color .18s,transform .18s}
[data-testid="stTopNavLink"]:hover{background:var(--fs-hover)!important;color:var(--fs-primary-dark)!important}
[data-testid="stTopNavLinkActive"]{background:var(--fs-primary-soft)!important;color:var(--fs-primary-dark)!important}
h1,h2,h3,h4{color:var(--fs-ink)!important;letter-spacing:-.035em}h1{font-weight:750!important}
[data-testid="stCaptionContainer"],[data-testid="stMarkdownContainer"] small{color:var(--fs-muted)!important}
[data-testid="stMarkdownContainer"] p{color:var(--fs-muted)}hr{border-color:var(--fs-line)!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--fs-surface)!important;border:1px solid var(--fs-line)!important;border-radius:20px!important;box-shadow:var(--fs-shadow)!important;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);transition:transform .18s,box-shadow .18s,border-color .18s}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:var(--fs-line-strong)!important;box-shadow:var(--fs-shadow)!important}
[data-testid="stDataFrame"]{border:1px solid var(--fs-line);border-radius:16px;overflow:hidden;box-shadow:var(--fs-shadow-soft);background:var(--fs-surface)}
[data-testid="stExpander"]{border:1px solid var(--fs-line)!important;border-radius:15px!important;background:var(--fs-surface)!important;box-shadow:var(--fs-shadow-soft),inset 0 1px 0 var(--fs-inset);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);overflow:visible}
[data-testid="stExpander"] details>summary{position:relative;min-height:3.1rem;padding:.35rem 2.8rem .35rem 1rem!important;font-weight:650!important;color:var(--fs-ink)!important;list-style:none!important}
[data-testid="stExpander"] details>summary::-webkit-details-marker{display:none}
[data-testid="stExpander"] details>summary svg{display:none!important}
[data-testid="stExpander"] details>summary:after{content:"+";position:absolute;right:1rem;top:50%;transform:translateY(-50%);display:grid;place-items:center;width:1.65rem;height:1.65rem;border-radius:50%;background:var(--fs-primary-soft);color:var(--fs-primary-dark);font-size:1.3rem;font-weight:500;line-height:1}
[data-testid="stExpander"] details[open]>summary:after{content:"−"}
[data-testid="stExpander"] details>summary:hover{background:var(--fs-hover)!important}
[class*="st-key-sd_chip_rec_"]{position:relative;overflow:visible!important;z-index:2}
[class*="st-key-sd_chip_rec_"] button{position:relative!important;overflow:visible!important}
[class*="st-key-sd_chip_rec_"] button:after{content:"Recommended";position:absolute;top:-.55rem;right:.7rem;z-index:5;padding:.24rem .65rem;border:1px solid var(--fs-primary-solid);border-radius:8px;background:var(--fs-primary-solid);color:#fff;font-size:.61rem;font-weight:750;letter-spacing:.035em;line-height:1.25;text-transform:uppercase;pointer-events:none;box-shadow:0 2px 8px rgba(50,30,20,.18)}
[class*="st-key-submission_card_"]{padding:1rem 1.15rem;border:1px solid var(--fs-line);border-radius:20px;background:linear-gradient(125deg,var(--fs-surface-strong),var(--fs-surface-soft));box-shadow:var(--fs-shadow-soft)}
.st-key-fs-site-footer{background:transparent!important}
.stButton>button,.stLinkButton>a,[data-testid="stDownloadButton"]>button{border-radius:12px!important;border:1px solid var(--fs-line-strong)!important;background:linear-gradient(180deg,var(--fs-surface-strong),var(--fs-surface-soft))!important;color:var(--fs-ink)!important;box-shadow:var(--fs-shadow-soft)!important;font-weight:600!important;transition:transform .16s,border-color .16s!important}
.stButton>button:hover,.stLinkButton>a:hover,[data-testid="stDownloadButton"]>button:hover{transform:translateY(-1px);border-color:var(--fs-primary)!important}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{background:var(--fs-primary-solid)!important;border-color:var(--fs-primary-solid)!important;color:var(--fs-primary-ink)!important;-webkit-text-fill-color:var(--fs-primary-ink)!important;box-shadow:var(--fs-shadow-soft)!important}
.stButton>button[kind="primary"] *, .stButton>button[data-testid="stBaseButton-primary"] *{color:var(--fs-primary-ink)!important;-webkit-text-fill-color:var(--fs-primary-ink)!important}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] [data-baseweb="select"],[data-testid="stMultiSelect"] [data-baseweb="select"],[data-testid="stFileUploader"] section{border-radius:12px!important;border-color:var(--fs-line-strong)!important;background:var(--fs-input)!important;color:var(--fs-ink)!important;box-shadow:inset 0 1px 3px rgba(35,24,17,.04)}
[data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus{border-color:var(--fs-primary)!important;box-shadow:0 0 0 3px var(--fs-primary-soft)!important}
[data-testid="stAlert"]{border-radius:14px!important;box-shadow:var(--fs-shadow-soft)}
.fs-row,.fs-grid{margin:4px 0 14px}.fs-row{display:flex;gap:14px;flex-wrap:wrap}.fs-grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}.fs-split{display:flex;align-items:center;justify-content:space-between;gap:16px}.fs-vr{width:1px;align-self:stretch;background:var(--fs-line)}
.fs-card{flex:1 1 160px;padding:18px 19px;border-radius:16px;border:1px solid var(--fs-line);border-top:3px solid var(--accent,var(--fs-primary));background:var(--fs-surface);box-shadow:var(--fs-shadow-soft),inset 0 1px 0 var(--fs-inset)}.fs-card.center{text-align:center}.fs-card.tint{background:color-mix(in srgb,var(--accent,var(--fs-primary)) 10%,var(--fs-surface-strong));border-color:color-mix(in srgb,var(--accent,var(--fs-primary)) 30%,var(--fs-line))}
.fs-label{font-size:13px;font-weight:600;opacity:.78;margin-bottom:7px;line-height:1.3}.fs-value{font-size:30px;font-weight:750;line-height:1;color:var(--accent,var(--fs-primary))}.fs-value.xl{font-size:38px}.fs-value.sm{font-size:17px;line-height:1.3}.fs-sub{font-size:12px;opacity:.7;margin-top:7px}
.fs-badge{display:inline-block;margin-left:6px;padding:2px 7px;border-radius:999px;font-size:10px;font-weight:700;background:var(--fs-primary-solid);color:#fff}.fs-pill{display:inline-block;padding:6px 12px;border-radius:999px;font-size:13px;font-weight:700;background:var(--fs-primary-solid);color:#fff}
.fs-tablewrap{overflow-x:auto;border:1px solid var(--fs-line);border-radius:15px;margin:8px 0 14px;background:var(--fs-surface)}.fs-table{width:100%;border-collapse:collapse;font-size:13px}.fs-table th{padding:11px 13px;text-align:left;font-size:12px;background:var(--fs-table-head)}.fs-table td{padding:11px 13px;border-top:1px solid var(--fs-line)}.fs-table .nowrap{white-space:nowrap;font-weight:500}.fs-table .num{text-align:center;font-size:15px;font-weight:700}.fs-table .mid{text-align:center;opacity:.75}
.fs-bar{height:10px;border-radius:8px;background:var(--fs-line);overflow:hidden}.fs-bar>div{height:100%;border-radius:8px}.fs-empty{padding:42px 20px;text-align:center;border:1px dashed var(--fs-line-strong);border-radius:18px;margin-top:8px;background:var(--fs-surface)}.fs-empty b{display:block;font-size:16px;margin-bottom:6px}.fs-empty span{opacity:.7;font-size:14px}
@media(max-width:720px){[data-testid="stMainBlockContainer"]{padding:1.25rem 1rem 0!important}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px!important}}
</style>
"""


def _is_dark_theme() -> bool:
    """FoldShield uses the light palette regardless of the browser or OS preference."""
    return False


def inject_css() -> None:
    palette = _PALETTES["dark" if _is_dark_theme() else "light"]
    css = _CSS.replace("__PALETTE__", palette)
    st.markdown(css, unsafe_allow_html=True)
