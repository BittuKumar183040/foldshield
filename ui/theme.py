"""Shared visual tokens and the global FoldShield stylesheet."""
import streamlit as st

GOOD, WARN, BAD, MUTED = "#2a9d8f", "#f4a261", "#e76f51", "#8794a3"
BRAND = "#168f91"
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


_CSS = """
<style>
:root{--fs-ink:#152b3a;--fs-muted:#627687;--fs-teal:#168f91;--fs-teal-dark:#08777a;--fs-line:rgba(47,91,112,.12);--fs-shadow:0 16px 42px rgba(28,69,88,.09),0 2px 8px rgba(28,69,88,.04)}
html,body,[data-testid="stAppViewContainer"]{background:#f4f8fa!important;color:var(--fs-ink)!important}
[data-testid="stAppViewContainer"]{background-image:radial-gradient(ellipse at 8% 0%,rgba(126,207,202,.2),transparent 33%),radial-gradient(ellipse at 95% 8%,rgba(154,196,226,.17),transparent 32%),linear-gradient(180deg,#f8fbfc 0%,#f1f6f8 100%)!important}
[data-testid="stHeader"]{background:rgba(248,251,252,.5)!important;backdrop-filter:blur(24px) saturate(145%)!important;-webkit-backdrop-filter:blur(24px) saturate(145%)!important;border-bottom:1px solid rgba(255,255,255,.55);box-shadow:0 8px 28px rgba(26,66,84,.045)}
[data-testid="stDeployButton"],button[data-testid="stMainMenu"],#MainMenu,[data-testid="stDecoration"]{display:none!important}
[data-testid="stMainBlockContainer"]{padding-top:2.2rem!important;padding-bottom:0!important}
[data-testid="stVerticalBlock"]{gap:1rem}
[data-testid="stNavigation"]{display:flex!important;visibility:visible!important;opacity:1!important;background:rgba(255,255,255,.48)!important;border:1px solid rgba(255,255,255,.78);border-bottom-color:var(--fs-line);box-shadow:0 5px 22px rgba(35,71,91,.06),inset 0 1px 0 rgba(255,255,255,.8);backdrop-filter:blur(28px) saturate(155%)!important;-webkit-backdrop-filter:blur(28px) saturate(155%)!important}
[data-testid="stTopNavLink"]{border-radius:999px!important;color:#456071!important;transition:background .18s,color .18s,transform .18s}
[data-testid="stTopNavLink"]:hover{background:rgba(22,143,145,.09)!important;color:var(--fs-teal-dark)!important}
[data-testid="stTopNavLinkActive"]{background:rgba(22,143,145,.12)!important;color:var(--fs-teal-dark)!important}
h1,h2,h3,h4{color:var(--fs-ink)!important;letter-spacing:-.035em}h1{font-weight:750!important}
[data-testid="stCaptionContainer"],[data-testid="stMarkdownContainer"] small{color:var(--fs-muted)!important}
[data-testid="stMarkdownContainer"] p{color:#425b6b}hr{border-color:var(--fs-line)!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,255,255,.76)!important;border:1px solid rgba(255,255,255,.94)!important;border-radius:20px!important;box-shadow:var(--fs-shadow)!important;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);transition:transform .18s,box-shadow .18s,border-color .18s}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:rgba(22,143,145,.2)!important;box-shadow:0 20px 48px rgba(28,69,88,.12),0 3px 10px rgba(28,69,88,.05)!important}
[data-testid="stDataFrame"]{border:1px solid rgba(255,255,255,.95);border-radius:18px;overflow:hidden;box-shadow:var(--fs-shadow);background:rgba(255,255,255,.88)}
[data-testid="stExpander"]{border:1px solid rgba(255,255,255,.88)!important;border-radius:15px!important;background:rgba(255,255,255,.53)!important;box-shadow:0 8px 24px rgba(31,76,96,.055),inset 0 1px 0 rgba(255,255,255,.9);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);overflow:visible}
[data-testid="stExpander"] details>summary{position:relative;min-height:3.1rem;padding:.35rem 2.8rem .35rem 1rem!important;font-weight:650!important;color:#294757!important;list-style:none!important}
[data-testid="stExpander"] details>summary::-webkit-details-marker{display:none}
[data-testid="stExpander"] details>summary svg{display:none!important}
[data-testid="stExpander"] details>summary:after{content:"+";position:absolute;right:1rem;top:50%;transform:translateY(-50%);display:grid;place-items:center;width:1.65rem;height:1.65rem;border-radius:50%;background:rgba(22,143,145,.1);color:#08777a;font-size:1.3rem;font-weight:500;line-height:1}
[data-testid="stExpander"] details[open]>summary:after{content:"−"}
[data-testid="stExpander"] details>summary:hover{background:rgba(22,143,145,.055)!important}
[class*="st-key-sd_chip_rec_"]{position:relative;overflow:visible!important;z-index:2}
[class*="st-key-sd_chip_rec_"] button{position:relative!important;overflow:visible!important}
[class*="st-key-sd_chip_rec_"] button:after{content:"Recommended";position:absolute;top:-.55rem;right:.7rem;z-index:5;padding:.24rem .65rem;border:1px solid rgba(255,255,255,.96);border-radius:8px;background:linear-gradient(135deg,rgba(232,255,251,.98),rgba(194,244,237,.96));color:#08777a;font-size:.61rem;font-weight:750;letter-spacing:.035em;line-height:1.25;text-transform:uppercase;box-shadow:0 4px 12px rgba(12,113,115,.2),0 1px 2px rgba(255,255,255,.9) inset;transform:rotate(1.5deg);pointer-events:none}
[class*="st-key-submission_card_"]{padding:1rem 1.15rem;border:1px solid rgba(255,255,255,.95);border-radius:20px;background:linear-gradient(125deg,rgba(255,255,255,.88),rgba(230,246,246,.72));box-shadow:var(--fs-shadow)}
.st-key-fs-site-footer{background:transparent!important}
.stButton>button,.stLinkButton>a,[data-testid="stDownloadButton"]>button{border-radius:12px!important;border:1px solid rgba(41,97,116,.14)!important;background:linear-gradient(180deg,#fff,rgba(239,247,249,.96))!important;color:#234454!important;box-shadow:0 3px 0 rgba(41,97,116,.08),0 7px 17px rgba(32,73,91,.07)!important;font-weight:600!important;transition:transform .16s,box-shadow .16s,border-color .16s!important}
.stButton>button:hover,.stLinkButton>a:hover,[data-testid="stDownloadButton"]>button:hover{transform:translateY(-1px);border-color:rgba(22,143,145,.42)!important;box-shadow:0 4px 0 rgba(22,143,145,.1),0 11px 22px rgba(32,73,91,.12)!important}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{background:linear-gradient(180deg,#29a9a5,#13898b)!important;border-color:rgba(8,119,122,.45)!important;color:#fff!important;-webkit-text-fill-color:#fff!important;box-shadow:0 3px 0 #08777a,0 9px 20px rgba(19,137,139,.22)!important}
.stButton>button[kind="primary"] *, .stButton>button[data-testid="stBaseButton-primary"] *{color:#fff!important;-webkit-text-fill-color:#fff!important}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"] [data-baseweb="select"],[data-testid="stMultiSelect"] [data-baseweb="select"],[data-testid="stFileUploader"] section{border-radius:12px!important;border-color:rgba(47,91,112,.18)!important;background:rgba(255,255,255,.78)!important;box-shadow:inset 0 1px 3px rgba(26,65,83,.04)}
[data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus{border-color:rgba(22,143,145,.64)!important;box-shadow:0 0 0 3px rgba(22,143,145,.11)!important}
[data-testid="stAlert"]{border-radius:14px!important;box-shadow:0 8px 24px rgba(28,69,88,.06)}
.fs-row,.fs-grid{margin:4px 0 14px}.fs-row{display:flex;gap:14px;flex-wrap:wrap}.fs-grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}.fs-split{display:flex;align-items:center;justify-content:space-between;gap:16px}.fs-vr{width:1px;align-self:stretch;background:var(--fs-line)}
.fs-card{flex:1 1 160px;padding:18px 19px;border-radius:16px;border:1px solid rgba(255,255,255,.95);border-top:3px solid var(--accent,#999);background:rgba(255,255,255,.78);box-shadow:0 10px 28px rgba(28,69,88,.07),inset 0 1px 0 white}.fs-card.center{text-align:center}.fs-card.tint{background:color-mix(in srgb,var(--accent) 9%,white);border-color:color-mix(in srgb,var(--accent) 24%,white)}
.fs-label{font-size:13px;font-weight:600;opacity:.75;margin-bottom:7px;line-height:1.3}.fs-value{font-size:30px;font-weight:750;line-height:1;color:var(--accent,inherit)}.fs-value.xl{font-size:38px}.fs-value.sm{font-size:17px;line-height:1.3}.fs-sub{font-size:12px;opacity:.65;margin-top:7px}
.fs-badge{display:inline-block;margin-left:6px;padding:2px 7px;border-radius:999px;font-size:10px;font-weight:700;background:rgba(46,117,182,.12);color:#2e75b6}.fs-pill{display:inline-block;padding:6px 12px;border-radius:999px;font-size:13px;font-weight:700;background:color-mix(in srgb,var(--accent) 13%,white);color:var(--accent)}
.fs-tablewrap{overflow-x:auto;border:1px solid var(--fs-line);border-radius:15px;margin:8px 0 14px;background:rgba(255,255,255,.8)}.fs-table{width:100%;border-collapse:collapse;font-size:13px}.fs-table th{padding:11px 13px;text-align:left;font-size:12px;background:rgba(22,143,145,.07)}.fs-table td{padding:11px 13px;border-top:1px solid var(--fs-line)}.fs-table .nowrap{white-space:nowrap;font-weight:500}.fs-table .num{text-align:center;font-size:15px;font-weight:700}.fs-table .mid{text-align:center;opacity:.75}
.fs-bar{height:10px;border-radius:8px;background:rgba(47,91,112,.12);overflow:hidden}.fs-bar>div{height:100%;border-radius:8px}.fs-empty{padding:42px 20px;text-align:center;border:1px dashed rgba(47,91,112,.25);border-radius:18px;margin-top:8px;background:rgba(255,255,255,.58)}.fs-empty b{display:block;font-size:16px;margin-bottom:6px}.fs-empty span{opacity:.7;font-size:14px}
@media(max-width:720px){[data-testid="stMainBlockContainer"]{padding:1.25rem 1rem 0!important}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px!important}}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
