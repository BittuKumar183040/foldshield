"""
FoldShield++ PDF Report Generator  (v2 — Phase 1 + Phase 2)
Uses reportlab Platypus for proper multi-page layout.
"""
import os, json, io, ntpath
from datetime import datetime

# ── matplotlib (figures page) ─────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from PIL import Image as PILImage

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage
)
from reportlab.platypus.flowables import Flowable


C_DARK      = colors.HexColor("#0D1B2A")
C_BLUE      = colors.HexColor("#185FA5")
C_GREEN     = colors.HexColor("#2a9d8f")
C_AMBER     = colors.HexColor("#f4a261")
C_RED       = colors.HexColor("#e76f51")
C_LIGHT_BG  = colors.HexColor("#F5F7FA")
C_BORDER    = colors.HexColor("#DDE1E7")
C_MUTED     = colors.HexColor("#6B7280")
C_P2_BG     = colors.HexColor("#EBF4FD")
C_P2_BORDER = colors.HexColor("#185FA5")
C_WHITE     = colors.white


def _score_color(val, invert=False):
    if val is None:
        return C_MUTED
    try:
        v = float(val)
    except Exception:
        return C_MUTED
    if invert:
        v = 1.0 - v / 5.0
    if v >= 0.66:
        return C_GREEN
    if v >= 0.33:
        return C_AMBER
    return C_RED


def _fmt(v, decimals=4):
    if v is None:
        return "n/a"
    try:
        return f"{float(v):.{decimals}f}"
    except Exception:
        return str(v)


def _safe_load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _pair_names(summary):
    """Extract clean PDB stem names, handling Windows paths."""
    inp = summary.get("inputs", {})
    rr  = inp.get("pdb_ref",   "") or ""
    qr  = inp.get("pdb_query", "") or ""
    rn  = ntpath.basename(rr).replace(".pdb","").replace(".PDB","")
    qn  = ntpath.basename(qr).replace(".pdb","").replace(".PDB","")
    if rn.lower().startswith("tmp"):
        rn = summary.get("ref_id") or summary.get("pdb_ref_id") or rn
    if qn.lower().startswith("tmp"):
        qn = summary.get("query_id") or summary.get("pdb_query_id") or qn
    return rn, qn


class ScoreBar(Flowable):
    def __init__(self, label, value, width=160*mm, height=10*mm, invert=False, vmax=1.0):
        super().__init__()
        self._label  = label
        self._value  = value
        self._width  = width
        self._height = height
        self._invert = invert
        self._vmax   = vmax
        self.width   = width
        self.height  = height + 6*mm

    def draw(self):
        c = self.canv
        v = None
        try:
            v = float(self._value) if self._value is not None else None
        except Exception:
            pass
        bar_w = self._width
        bar_h = 5*mm
        y_bar = 4*mm
        fill  = _score_color(v, invert=self._invert)
        c.setFillColor(C_LIGHT_BG)
        c.setStrokeColor(C_BORDER)
        c.roundRect(0, y_bar, bar_w, bar_h, 2*mm, fill=1, stroke=1)
        if v is not None:
            portion = min(1.0, max(0.0, v / self._vmax))
            if self._invert:
                portion = 1.0 - portion
            if portion > 0:
                c.setFillColor(fill)
                c.setStrokeColor(fill)
                c.roundRect(0, y_bar, bar_w * portion, bar_h, 2*mm, fill=1, stroke=0)
        c.setFont("Helvetica", 8)
        c.setFillColor(C_DARK)
        c.drawString(0, y_bar + bar_h + 1.5*mm, self._label)
        val_txt = _fmt(v, 3) if v is not None else "n/a"
        c.setFillColor(fill if v is not None else C_MUTED)
        c.drawRightString(bar_w, y_bar + bar_h + 1.5*mm, val_txt)


def _build_styles():
    base = getSampleStyleSheet()
    s = {}
    s["title"]    = ParagraphStyle("FSTitle",    parent=base["Title"],
                        fontSize=20, textColor=C_DARK, spaceAfter=4, leading=26)
    s["subtitle"] = ParagraphStyle("FSSubtitle", parent=base["Normal"],
                        fontSize=9,  textColor=C_MUTED, spaceAfter=6, leading=13)
    s["h2"]       = ParagraphStyle("FSH2",       parent=base["Heading2"],
                        fontSize=12, textColor=C_BLUE, spaceBefore=8, spaceAfter=3, leading=15)
    s["h3"]       = ParagraphStyle("FSH3",       parent=base["Heading3"],
                        fontSize=10, textColor=C_DARK, spaceBefore=5, spaceAfter=2,
                        fontName="Helvetica-Bold", leading=13)
    s["body"]     = ParagraphStyle("FSBody",     parent=base["Normal"],
                        fontSize=9,  textColor=C_DARK, leading=12, spaceAfter=3)
    s["caption"]  = ParagraphStyle("FSCaption",  parent=base["Normal"],
                        fontSize=7.5, textColor=C_MUTED, leading=11, spaceAfter=4)
    s["flag"]     = ParagraphStyle("FSFlag",     parent=base["Normal"],
                        fontSize=8,  textColor=C_AMBER, leading=12,
                        leftIndent=8, spaceAfter=2)
    return s


def _cell(txt, bold=False, align=TA_LEFT, size=8, color=C_DARK):
    return Paragraph(str(txt),
        ParagraphStyle("c", fontSize=size, textColor=color, alignment=align,
                       leading=11, fontName="Helvetica-Bold" if bold else "Helvetica"))


def _score_cell(val, decimals=3, invert=False):
    col = _score_color(val, invert=invert)
    return Paragraph(f"<b>{_fmt(val, decimals)}</b>",
        ParagraphStyle("sv", fontSize=9, textColor=col,
                       alignment=TA_CENTER, leading=12))


def _on_page(canvas, doc, pdb_ref, pdb_qry):
    canvas.saveState()
    W, H = A4
    canvas.setStrokeColor(C_BLUE)
    canvas.setLineWidth(0.5)
    canvas.line(15*mm, H - 12*mm, W - 15*mm, H - 12*mm)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(C_BLUE)
    canvas.drawString(15*mm, H - 10*mm, "FoldShield++  Protein Structural Analysis Report")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(W - 15*mm, H - 10*mm, f"Page {doc.page}")
    canvas.setStrokeColor(C_BORDER)
    canvas.line(15*mm, 10*mm, W - 15*mm, 10*mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(15*mm, 6*mm,
        f"Ref: {os.path.basename(str(pdb_ref))}   Query: {os.path.basename(str(pdb_qry))}")
    canvas.drawRightString(W - 15*mm, 6*mm,
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.restoreState()


_DISPLAY_TO_KEY = {
    "Braid similarity":              "braid",
    "Motif similarity (UL-DSL)":     "motif",
    "Global topology":               "topology",
    "Local topology (Phase 2)":      "local_topo",
    "SSEF entropy (Phase 2)":        "ssef",
    "Persistent homology (Phase 3)": "ph",
}


# ─────────────────────────────────────────────────────────────────────────────
# NEW: Figures page — Figure 1 (bar chart) + Figure 2 (radar chart)
# ─────────────────────────────────────────────────────────────────────────────

def _build_figures_png(summary: dict, out_path: str):
    """
    Renders Figure 1 (grouped bar) and Figure 2 (radar) side by side
    and saves as a PNG. Returns out_path on success, None on failure.
    """
    try:
        sig      = summary.get("fusion", {}).get("signal_scores", {})
        combined = float(
            summary.get("combined_similarity") or
            summary.get("fusion", {}).get("combined_score") or 0
        )

        KEYS    = ["braid", "motif", "topology", "local_topo", "ssef"]
        LABELS  = ["Braid", "Motif", "Global\nTopo", "Local\nTopo", "SSEF"]
        RLABELS = ["Braid", "Motif", "Global Topo", "Local Topo", "SSEF"]
        # per-signal colours — Local Topo red per Marcos's request
        BAR_COLORS = ["#4C72B0", "#55A868", "#8172B2", "#C44E52", "#CCB974"]
        COMBINED_COLOR = "#0D1B2A"

        values = [float(sig.get(k, 0) or 0) for k in KEYS]
        rn, qn = _pair_names(summary)
        pair_label = f"{rn}  vs  {qn}"

        fig, (ax1, ax2) = plt.subplots(
            1, 2, figsize=(13, 6),
            facecolor="white",
            gridspec_kw={"width_ratios": [1.2, 1]}
        )
        fig.suptitle(
            f"FoldShield++  |  Signal Analysis  |  {pair_label}",
            fontsize=12, fontweight="bold", color="#0D1B2A", y=1.01
        )

        # ── Figure 1: Bar chart ───────────────────────────────────────────
        bar_labels = LABELS + ["Combined"]
        bar_vals   = values + [combined]
        bar_colors = BAR_COLORS + [COMBINED_COLOR]

        bars = ax1.bar(bar_labels, bar_vals, color=bar_colors,
                       edgecolor="white", linewidth=0.5, width=0.62)

        ax1.set_ylim(0, 1.22)
        ax1.set_ylabel("Score", fontsize=9)
        ax1.set_title("Figure 1. FoldShield++ Signal Scores by Pair",
                      fontsize=10, fontweight="bold", pad=10)
        ax1.axhline(0.75, color="#aaaaaa", linewidth=0.8,
                    linestyle="--", alpha=0.7, label="0.75 threshold")
        ax1.axhline(0.50, color="#cccccc", linewidth=0.8,
                    linestyle=":",  alpha=0.7, label="0.50 threshold")
        ax1.tick_params(axis="x", labelsize=8.5)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax1.set_facecolor("white")
        ax1.yaxis.grid(True, color="#eeeeee", linewidth=0.6, zorder=0)
        ax1.set_axisbelow(True)

        for bar, val in zip(bars, bar_vals):
            ax1.text(
                bar.get_x() + bar.get_width() / 2, val + 0.03,
                f"{val:.3f}", ha="center", va="bottom", fontsize=8,
                fontweight="bold"
            )

        ax1.legend(fontsize=7, loc="upper right", framealpha=0.7)
        ax1.text(
            0.01, 0.02,
            "Local Topo (red) highlights changes\ngeometry-only metrics miss\n"
            "Error bars not shown — deterministic scores",
            transform=ax1.transAxes, fontsize=6.5,
            color="#6B7280", va="bottom"
        )

        # ── Figure 2: Radar chart ─────────────────────────────────────────
        angles        = np.linspace(0, 2 * np.pi, len(RLABELS), endpoint=False).tolist()
        vals_closed   = values + [values[0]]
        angles_closed = angles + [angles[0]]

        ax2 = plt.subplot(122, polar=True)
        ax2.plot(angles_closed, vals_closed, color="#185FA5", linewidth=2.0)
        ax2.fill(angles_closed, vals_closed, color="#185FA5", alpha=0.18)

        # reference ring at 0.75
        ref_ring = [0.75] * len(RLABELS) + [0.75]
        ax2.plot(angles_closed, ref_ring, color="#aaaaaa",
                 linewidth=0.8, linestyle="--", alpha=0.6)

        ax2.set_xticks(angles)
        ax2.set_xticklabels(RLABELS, fontsize=9)
        ax2.set_ylim(0, 1)
        ax2.set_yticks([0.25, 0.50, 0.75, 1.0])
        ax2.set_yticklabels(["0.25", "0.50", "0.75", "1.0"], fontsize=6.5)
        ax2.grid(color="#dddddd", linestyle=":", linewidth=0.6)
        ax2.set_title("Figure 2. FoldShield++ Signal Profile",
                      fontsize=10, fontweight="bold", pad=18)
        ax2.text(
            0.5, -0.14,
            "Balanced fill = all signals agree\n"
            "Collapsed axis = signal detects unique structural change",
            transform=ax2.transAxes, fontsize=7,
            color="#6B7280", ha="center"
        )

        plt.tight_layout(pad=1.5)
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return out_path

    except Exception as e:
        print(f"[report] _build_figures_png failed: {e}")
        try:
            plt.close("all")
        except Exception:
            pass
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point  (original + figures page appended)
# ─────────────────────────────────────────────────────────────────────────────

def create_pdf_report(summary_json_path, image_paths, out_pdf_path):
    if not os.path.exists(summary_json_path):
        raise FileNotFoundError(f"summary.json not found: {summary_json_path}")

    summary = _safe_load_json(summary_json_path)
    styles  = _build_styles()

    inputs   = summary.get("inputs", {})
    pdb_ref  = inputs.get("pdb_ref",  "")
    pdb_qry  = inputs.get("pdb_query","")
    mode     = inputs.get("mode",     "")
    tm       = summary.get("tm_score")
    rmsd     = summary.get("rmsd")
    sym      = summary.get("Symbolic_score_metrics", {}) or {}
    fusion   = summary.get("fusion", {}) or {}
    p2       = summary.get("phase2", {}) or {}

    on_page = lambda c, d: _on_page(c, d, pdb_ref, pdb_qry)

    doc = SimpleDocTemplate(out_pdf_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=18*mm, bottomMargin=16*mm)

    story = []

    # ── PAGE 1 ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("FoldShield<super>++</super>  Structural Analysis Report",
                            styles["title"]))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  "
        f"Mode: {mode}  ·  RexCrux Research Laboratory",
        styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_BLUE, spaceAfter=5))

    # Inputs
    story.append(Paragraph("Input Structures", styles["h2"]))
    story.append(Table([
        [_cell("Reference PDB", bold=True), _cell(os.path.basename(str(pdb_ref)))],
        [_cell("Query PDB",     bold=True), _cell(os.path.basename(str(pdb_qry)))],
        [_cell("Mode",          bold=True), _cell(mode)],
        [_cell("Ref chain",     bold=True), _cell(inputs.get("ref_chain_id","A"))],
        [_cell("Query chain",   bold=True), _cell(inputs.get("query_chain_id","A"))],
    ], colWidths=[45*mm, 135*mm],
    style=TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_WHITE, C_LIGHT_BG]),
        ("GRID",    (0,0),(-1,-1), 0.3, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
    ])))
    story.append(Spacer(1, 4*mm))

    # Classical
    story.append(Paragraph("Classical Coordinate Metrics", styles["h2"]))
    story.append(Paragraph(
        "These metrics saturate near 1.0 even when function diverges. "
        "Use FoldShield++ signals below for structural perturbation insight.",
        styles["caption"]))
    story.append(Table([
        [_cell("Metric",bold=True),_cell("Value",bold=True,align=TA_CENTER),_cell("Note",bold=True)],
        [_cell("TM-score"), _score_cell(tm),
         _cell(">=0.50 same fold  ·  >=0.90 nearly identical")],
        [_cell("RMSD (A)"), _score_cell(rmsd, invert=True),
         _cell("Lower is better  ·  >3.0 A = significant deviation")],
    ], colWidths=[40*mm, 28*mm, 112*mm],
    style=TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_BLUE),
        ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE, C_LIGHT_BG]),
        ("GRID",          (0,0),(-1,-1), 0.3, C_BORDER),
        ("ALIGN",         (1,0),(1,-1),"CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1),5),
        ("BOTTOMPADDING", (0,0),(-1,-1),5),
        ("LEFTPADDING",   (0,0),(-1,-1),6),
    ])))
    story.append(Spacer(1, 4*mm))

    # All signals table
    story.append(Paragraph("FoldShield++ Signal Scores — Phase 1 + Phase 2", styles["h2"]))
    story.append(Paragraph(
        "All active signals with scores, fusion weights, and interpretation. "
        "Phase 2 signals are highlighted in blue.",
        styles["caption"]))

    signal_scores = fusion.get("signal_scores", {})
    weights_used  = fusion.get("weights_used",  {})
    per_signal    = fusion.get("per_signal",     {})

    sig_rows = [[_cell("Signal",bold=True), _cell("Score",bold=True,align=TA_CENTER),
                 _cell("Weight",bold=True,align=TA_CENTER), _cell("Interpretation",bold=True)]]

    p2_row_cmds = []
    row_idx = 1
    if signal_scores and per_signal:
        for display_name, interp_text in per_signal.items():
            key   = _DISPLAY_TO_KEY.get(display_name, "")
            val   = signal_scores.get(key)
            w     = weights_used.get(key, 0.0)
            is_p2 = "Phase 2" in display_name or "Phase 3" in display_name
            name_p = Paragraph(
                f"<b>{display_name}</b>" +
                (" <font color='#185FA5' size='7'>[P2]</font>" if is_p2 else ""),
                ParagraphStyle("sn", fontSize=8, leading=11,
                               textColor=C_BLUE if is_p2 else C_DARK))
            sig_rows.append([name_p, _score_cell(val),
                              _cell(f"{w:.2f}", align=TA_CENTER, size=8),
                              _cell(interp_text, size=8)])
            if is_p2:
                p2_row_cmds += [
                    ("BACKGROUND", (0,row_idx),(-1,row_idx), C_P2_BG),
                    ("LINEBELOW",  (0,row_idx),(-1,row_idx), 0.5, C_P2_BORDER),
                ]
            row_idx += 1
    else:
        for lbl, key in [("Symbolic Score","Symbolic Similarity Score"),
                          ("Entropy Map","Behavioural Correlation Similarity"),
                          ("Topology","Structural Topology Similarity"),
                          ("Topology Ordering","Structural Topology Ordering Similarity")]:
            sig_rows.append([_cell(lbl,size=8), _score_cell(sym.get(key)),
                              _cell("—",align=TA_CENTER,size=8), _cell("—",size=8)])

    sig_tbl = Table(sig_rows, colWidths=[60*mm, 22*mm, 20*mm, 78*mm])
    sig_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_DARK),
        ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE, C_LIGHT_BG]),
        ("GRID",          (0,0),(-1,-1), 0.3, C_BORDER),
        ("ALIGN",         (1,0),(2,-1),"CENTER"),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1),5),
        ("BOTTOMPADDING", (0,0),(-1,-1),5),
        ("LEFTPADDING",   (0,0),(-1,-1),6),
    ] + p2_row_cmds))
    story.append(sig_tbl)
    story.append(Spacer(1, 4*mm))

    # Combined score + verdict
    story.append(Paragraph("Fusion Layer v2 — Combined Score", styles["h2"]))
    combined_score = fusion.get("combined_score") or summary.get("combined_similarity")
    fusion_mode    = fusion.get("fusion_mode", "—")
    overall        = fusion.get("overall") or summary.get("interpreted_combined_similarity","—")
    flags          = fusion.get("flags", [])

    story.append(Table([
        [_cell("Combined score",bold=True), _cell("Fusion mode",bold=True),
         _cell("Overall verdict",bold=True)],
        [_score_cell(combined_score, decimals=4),
         _cell(fusion_mode, size=8),
         _cell(overall, bold=True, size=9, color=_score_color(combined_score))],
    ], colWidths=[35*mm, 35*mm, 110*mm],
    style=TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_DARK),
        ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
        ("BACKGROUND",    (0,1),(-1,1), C_LIGHT_BG),
        ("GRID",          (0,0),(-1,-1), 0.3, C_BORDER),
        ("ALIGN",         (0,0),(1,-1),"CENTER"),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1),6),
        ("BOTTOMPADDING", (0,0),(-1,-1),6),
        ("LEFTPADDING",   (0,0),(-1,-1),8),
    ])))

    for flag in flags:
        story.append(Paragraph(f"   {flag}", styles["flag"]))

    story.append(Spacer(1, 4*mm))

    # Phase 2 perturbation class
    if p2:
        story.append(Paragraph("Phase 2 — Perturbation Classification", styles["h2"]))
        gap     = p2.get("gap_score")
        p_class = p2.get("perturbation_class", "—")
        ssef_v  = p2.get("ssef_score")
        loc_v   = p2.get("local_topology_score")
        gap_col = _score_color(1.0 - abs(gap) if gap is not None else None)

        story.append(Table([
            [_cell("SSEF score",bold=True), _cell("Local topology",bold=True),
             _cell("Gap score",bold=True),  _cell("Perturbation class",bold=True)],
            [_score_cell(ssef_v), _score_cell(loc_v),
             Paragraph(f"<b>{_fmt(gap,3)}</b>",
                 ParagraphStyle("gs",fontSize=10,textColor=gap_col,
                                alignment=TA_CENTER,leading=13)),
             _cell(p_class, bold=True, size=9, color=gap_col)],
        ], colWidths=[30*mm, 30*mm, 25*mm, 95*mm],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), C_P2_BORDER),
            ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
            ("BACKGROUND",    (0,1),(-1,1), C_P2_BG),
            ("GRID",          (0,0),(-1,-1), 0.5, C_P2_BORDER),
            ("ALIGN",         (0,0),(2,-1),"CENTER"),
            ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1),6),
            ("BOTTOMPADDING", (0,0),(-1,-1),6),
            ("LEFTPADDING",   (0,0),(-1,-1),8),
        ])))
        story.append(Paragraph(
            "Gap = SSEF minus local topology.  "
            "<0.15 buried-core mutation  |  0.15-0.36 fold-switch  |  >0.36 conformational transition",
            styles["caption"]))
        if p2.get("local_topology_unreliable"):
            story.append(Paragraph(
                "Warning: Local topology flagged unreliable — large length mismatch.",
                styles["flag"]))
        if p2.get("ssef_note"):
            story.append(Paragraph(f"Warning: {p2['ssef_note']}", styles["flag"]))

    # ── PAGE 2 ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Entropy Maps & Signal Profiles", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))

    valid_imgs = [p for p in (image_paths or []) if p and os.path.exists(p)]
    if valid_imgs:
        W_page   = A4[0] - 30*mm
        n        = min(len(valid_imgs), 3)
        thumb_w  = (W_page - (n-1)*3*mm) / n
        img_row  = []
        for path in valid_imgs[:n]:
            try:
                img_row.append(RLImage(path, width=thumb_w, height=thumb_w * 0.65))
            except Exception:
                img_row.append(_cell(f"[{os.path.basename(path)}]", size=7, color=C_MUTED))
        tbl = Table([img_row], colWidths=[thumb_w]*n)
        tbl.setStyle(TableStyle([
            ("ALIGN",         (0,0),(-1,-1),"CENTER"),
            ("GRID",          (0,0),(-1,-1), 0.3, C_BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ]))
        story.append(tbl)
        story.append(Paragraph(
            "Left to right: Entropy ref  ·  Entropy query  ·  Patchwise NCC",
            styles["caption"]))
        story.append(Spacer(1, 5*mm))

    # Score bars
    story.append(Paragraph("Signal Score Bars", styles["h3"]))
    story.append(Paragraph(
        "Visual 0-1 scale for all active signals. Green >= 0.66 / Amber 0.33-0.66 / Red < 0.33.",
        styles["caption"]))

    bar_w = A4[0] - 30*mm
    for lbl, val, inv, vmax in [("TM-score", tm, False, 1.0), ("RMSD (A)", rmsd, True, 5.0)]:
        story.append(ScoreBar(lbl, val, width=bar_w, invert=inv, vmax=vmax))
    if signal_scores:
        for dn, key in _DISPLAY_TO_KEY.items():
            v = signal_scores.get(key)
            if v is not None:
                story.append(ScoreBar(dn, v, width=bar_w))
    if combined_score is not None:
        story.append(ScoreBar("Combined (Fusion v2)", combined_score, width=bar_w))

    story.append(Spacer(1, 5*mm))

    # Symbolic detail
    if sym:
        story.append(Paragraph("Symbolic Score Detail", styles["h3"]))
        interp_sym = summary.get("interpreted_symbolic_scores", {}) or {}
        s_rows = [[_cell("Metric",bold=True), _cell("Value",bold=True,align=TA_CENTER),
                   _cell("Interpretation",bold=True)]]
        for display, ikey in [
            ("Symbolic Similarity Score",
             "Symbolic Similarity Score"),
            ("Behavioural Correlation Similarity",
             "Behavioural Correlation Similarity_Entropy Map patchwise NCC"),
            ("Structural Topology Similarity",
             "Structural Topology Similarity_Jaccard_generators"),
            ("Structural Topology Ordering Similarity",
             "Structural Topology Ordering Similarity_Pattern_similarity"),
        ]:
            s_rows.append([_cell(display,size=8), _score_cell(sym.get(display)),
                           _cell(interp_sym.get(ikey,"—"), size=8)])
        s_tbl = Table(s_rows, colWidths=[70*mm, 25*mm, 85*mm])
        s_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), C_DARK),
            ("TEXTCOLOR",     (0,0),(-1,0), C_WHITE),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE, C_LIGHT_BG]),
            ("GRID",          (0,0),(-1,-1), 0.3, C_BORDER),
            ("ALIGN",         (1,0),(1,-1),"CENTER"),
            ("TOPPADDING",    (0,0),(-1,-1),4),
            ("BOTTOMPADDING", (0,0),(-1,-1),4),
            ("LEFTPADDING",   (0,0),(-1,-1),6),
        ]))
        story.append(s_tbl)

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
    story.append(Paragraph(
        "FoldShield++ Phase 2  |  RexCrux Research Laboratory  |  "
        "Signals: Braid / UL-DSL / Global Topology / Local Topology / SSEF Entropy  |  "
        "Fusion: Ridge Regression weighted linear combination",
        styles["caption"]))

    # ── PAGE 3: Figure 1 (bar) + Figure 2 (radar) ─────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Signal Analysis — Figures", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=6))

    tmp_png = os.path.join(
        os.path.dirname(os.path.abspath(out_pdf_path)), "_figs_tmp.png"
    )
    fig_path = _build_figures_png(summary, tmp_png)

    if fig_path and os.path.exists(fig_path):
        try:
            # Load via PIL → BytesIO so ReportLab reads from memory, not the path
            avail_w = A4[0] - 30 * mm
            pil_img = PILImage.open(fig_path).convert("RGB")
            iw, ih  = pil_img.size
            ratio   = avail_w / iw
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            buf.seek(0)
            story.append(RLImage(buf, width=avail_w, height=ih * ratio))
            story.append(Paragraph(
                "Figure 1: Bar chart comparing all five signals and the Combined score. "
                "Local Topo (red) highlights structural changes geometry-only metrics miss. "
                "Dashed = 0.75 · Dotted = 0.50. Error bars not shown — scores are deterministic.  "
                "Figure 2: Radar chart showing the five-signal profile. "
                "Balanced fill = all signals agree. Collapsed axis = signal detects unique structural change.",
                styles["caption"]
            ))
        except Exception as e:
            story.append(Paragraph(f"(Figure rendering error: {e})", styles["flag"]))
        finally:
            try: os.remove(fig_path)
            except Exception: pass
    else:
        story.append(Paragraph(
            "(Figures could not be generated — check matplotlib/numpy installation.)",
            styles["flag"]
        ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


if __name__ == "__main__":
    summary_json = "results/topo-similarity-integrated_1crn_vs_1tim/summary.json"
    images = [
        "results/topo-similarity-integrated_1crn_vs_1tim/entropy_ref.png",
        "results/topo-similarity-integrated_1crn_vs_1tim/entropy_query.png",
        "results/topo-similarity-integrated_1crn_vs_1tim/entropy_patchwise_ncc.png",
    ]
    out_pdf = "results/topo-similarity-integrated_1crn_vs_1tim/similarity_report.pdf"
    create_pdf_report(summary_json, images, out_pdf)
    print(f"Report generated: {out_pdf}")