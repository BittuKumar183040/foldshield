# app.py
import os, io, json, tempfile, shutil, subprocess, sys, pathlib, contextlib, time
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from core.pdb.pdb_precheck import analyze_pdb
from core.similarity.fusion_layer import SignalNormalizer, RidgeFusionLayer
from visualisation.visualise_feature_extractor import plot_dual_pdb_token_backbones_plotly_separate

st.set_page_config(page_title="FoldShield++", layout="wide")
st.title("FoldShield++ — Protein Similarity Demo")

# ── Fusion layer — load once at startup ───────────────────────────────────────
_YAML_PATH   = os.path.join(os.path.dirname(__file__), "configs", "weights_phase2.yaml")
_normalizer  = SignalNormalizer.from_yaml(_YAML_PATH)
_ridge_layer = RidgeFusionLayer(weights_yaml=_YAML_PATH, mode="phase2")

# ---------- Sidebar: inputs ----------
st.sidebar.header("Inputs")
mode        = st.sidebar.radio("Coordinate mode", ["ca", "sequence"], index=0)
keep_hetatm = st.sidebar.checkbox("Keep HETATM", value=False)
pdb_ref_up   = st.sidebar.file_uploader("Reference PDB", type=["pdb"])
pdb_query_up = st.sidebar.file_uploader("Query PDB", type=["pdb"])
st.sidebar.caption("Or load a previously computed summary.json")
summary_upload = st.sidebar.file_uploader("summary.json (optional)", type=["json"])
run_btn = st.sidebar.button("Run pipeline", type="primary", use_container_width=True)

# ---------- Helper: write uploaded file to tmp ----------
def write_tmp(uploaded, suffix=".pdb"):
    if not uploaded: return None
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(uploaded.read())
    return path

# ---------- Helper: colored meter ----------
def meter(label, value, *, higher_is_better=True, lo=0.0, hi=1.0):
    if value is None:
        st.markdown(f"**{label}:** —")
        return
    try:
        v = float(value)
    except Exception:
        st.markdown(f"**{label}:** —")
        return
    v_norm = (v - lo) / max(1e-9, (hi - lo))
    v_norm = max(0.0, min(1.0, v_norm))
    if not higher_is_better:
        v_norm = 1.0 - v_norm
    if v_norm < 0.33:   color = "#e76f51"
    elif v_norm < 0.66: color = "#f4a261"
    else:               color = "#2a9d8f"
    pct = int(round(v_norm * 100))
    html = f"""
    <div style="margin:4px 0 12px 0;">
      <div style="display:flex;justify-content:space-between;font-weight:600;">
        <span>{label}</span><span>{v:.3f}</span>
      </div>
      <div style="height:10px;background:#eee;border-radius:8px;">
        <div style="height:10px;width:{pct}%;background:{color};border-radius:8px;"></div>
      </div>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)

# ---------- Gauge ----------
def gauge(label: str, value, *, vmin=0.0, vmax=1.0, invert=False, suffix=""):
    if value is None:
        st.markdown(f"**{label}:** —")
        return
    try:
        v = float(value)
    except Exception:
        st.markdown(f"**{label}:** —")
        return
    lo = vmin + 0.33*(vmax - vmin)
    hi = vmin + 0.66*(vmax - vmin)
    steps = [
        {'range': [vmin, lo], 'color': '#e76f51'},
        {'range': [lo, hi],   'color': '#f4a261'},
        {'range': [hi, vmax], 'color': '#2a9d8f'},
    ]
    if invert:
        steps = list(reversed(steps))
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=v,
        title={'text': label},
        number={'suffix': suffix, 'valueformat': '.3f'},
        gauge={'axis': {'range': [vmin, vmax]}, 'bar': {'color': '#264653'}, 'steps': steps}
    ))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

# ---------- Tabs ----------
tab_visuals, tab_results, tab_log = st.tabs(["Visuals", "Results", "Log"])
log_text      = ""
summary       = None
artifacts_dir = None

# ---------- Utility: load summary from uploaded JSON ----------
def try_load_summary_from_upload(upload):
    try:
        data   = json.loads(upload.read().decode("utf-8"))
        outdir = data.get("inputs", {}).get("outdir")
        return data, outdir
    except Exception as e:
        st.error(f"Failed to parse summary.json: {e}")
        return None, None

# ---------- Run pipeline in-process ----------
def run_pipeline_inproc(pdb_ref_path, pdb_query_path, mode, keep_hetatm,
                         ref_chain_id=None, query_chain_id=None):
    work   = tempfile.mkdtemp(prefix="foldshield_")
    outdir = os.path.join(work, "results")
    os.makedirs(outdir, exist_ok=True)

    cfg = {
        "pdb_ref":        pdb_ref_path,
        "pdb_query":      pdb_query_path,
        "outdir":         outdir,
        "keep_hetatm":    bool(keep_hetatm),
        "mode":           mode,
        "ref_chain_id":   ref_chain_id,
        "query_chain_id": query_chain_id
    }

    from main import main as foldshield_main
    buf = io.StringIO()
    try:
        foldshield_main(cfg)
    except Exception as e:
        log = buf.getvalue() + f"\n\nERROR: {e}"
        return None, outdir, log, work

    log          = buf.getvalue()
    summary_path = os.path.join(outdir, "summary.json")
    summary      = None
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            summary = json.load(f)
    return summary, outdir, log, work

# ---------- Chain extraction ----------
def analyze_and_store_chains(tmp_ref_path, tmp_qry_path):
    try:
        rrep       = analyze_pdb(tmp_ref_path)
        qrep       = analyze_pdb(tmp_qry_path)
        ref_chains = rrep['chain_ids']
        qry_chains = qrep['chain_ids']
    except Exception as e:
        st.warning(f"analyze_pdb failed: {e}")
        ref_chains = qry_chains = []
    return ref_chains, qry_chains

# ---------- Controller ----------
if summary_upload:
    summary, artifacts_dir = try_load_summary_from_upload(summary_upload)

tmp_ref_path = None
tmp_qry_path = None
ref_chains   = []
qry_chains   = []

if pdb_ref_up and pdb_query_up:
    tmp_ref_path = write_tmp(pdb_ref_up, ".pdb")
    tmp_qry_path = write_tmp(pdb_query_up, ".pdb")
    ref_chains, qry_chains = analyze_and_store_chains(tmp_ref_path, tmp_qry_path)
    st.session_state['tmp_ref_path'] = tmp_ref_path
    st.session_state['tmp_qry_path'] = tmp_qry_path
    st.session_state['ref_chains']   = ref_chains
    st.session_state['qry_chains']   = qry_chains
else:
    tmp_ref_path = st.session_state.get('tmp_ref_path')
    tmp_qry_path = st.session_state.get('tmp_qry_path')
    ref_chains   = st.session_state.get('ref_chains', [])
    qry_chains   = st.session_state.get('qry_chains', [])

# ---------- Chain selectors UI ----------
c1, c2 = st.columns(2)
with c1:
    st.subheader("Reference chain")
    ref_chain_selected = (st.selectbox("Choose ref chain", options=ref_chains, index=0)
                          if ref_chains else st.text_input("Ref chain", value="A"))
with c2:
    st.subheader("Query chain")
    qry_chain_selected = (st.selectbox("Choose query chain", options=qry_chains, index=0)
                          if qry_chains else st.text_input("Query chain", value="A"))

# ---------- Run button ----------
if run_btn:
    if not tmp_ref_path or not tmp_qry_path:
        st.error("Upload both PDB files first.")
    else:
        with st.spinner("Running FoldShield pipeline..."):
            summary, artifacts_dir, log_text, workdir = run_pipeline_inproc(
                tmp_ref_path, tmp_qry_path, mode, keep_hetatm,
                ref_chain_id=ref_chain_selected, query_chain_id=qry_chain_selected
            )
            st.session_state['last_artifacts'] = artifacts_dir
        if summary is None:
            st.error("Run finished but summary not found. Check the Log tab.")
        else:
            st.success("Run finished. Summary loaded.")

# ---------- RESULTS TAB ----------
with tab_results:
    st.subheader("Results")
    if not summary:
        st.info("Upload a summary.json or run the pipeline from the sidebar.")
    else:
        fusion  = summary.get("fusion", {})
        p2      = summary.get("phase2", {})
        sym     = summary.get("Symbolic_score_metrics", {}) or {}

        signal_scores = fusion.get("signal_scores", {})
        weights_used  = fusion.get("weights_used",  {})
        per_signal    = fusion.get("per_signal",     {})

        _DISPLAY_TO_KEY = {
            "Braid similarity":              "braid",
            "Motif similarity (UL-DSL)":     "motif",
            "Global topology":               "topology",
            "Local topology (Phase 2)":      "local_topo",
            "SSEF entropy (Phase 2)":        "ssef",
            "Persistent homology (Phase 3)": "ph",
        }

        def _color(v, invert=False):
            try:
                f = float(v)
                if invert: f = 1.0 - f/5.0
                if f >= 0.66: return "#2a9d8f"
                if f >= 0.33: return "#f4a261"
                return "#e76f51"
            except Exception:
                return "#999"

        # ── Classical metrics ─────────────────────────────────────────────
        st.markdown("#### Coordinate baseline")
        tm   = summary.get("tm_score")
        rmsd = summary.get("rmsd")
        tm_c   = _color(tm)
        rmsd_c = _color(rmsd, invert=True)
        tm_str   = f"{tm:.4f}"   if tm   is not None else "—"
        rmsd_str = f"{rmsd:.3f}" if rmsd is not None else "—"
        st.markdown(f"""
        <div style="display:flex;gap:16px;margin-bottom:6px;">
          <div style="flex:1;border:1px solid #e0e0e0;border-top:4px solid {tm_c};
                      border-radius:8px;padding:16px 20px;">
            <div style="font-size:13px;color:#444;font-weight:500;margin-bottom:6px;">TM-score</div>
            <div style="font-size:36px;font-weight:700;color:{tm_c};line-height:1;">{tm_str}</div>
            <div style="font-size:12px;color:#666;margin-top:6px;">
              >= 0.90 nearly identical &nbsp;·&nbsp; >= 0.50 same fold</div>
          </div>
          <div style="flex:1;border:1px solid #e0e0e0;border-top:4px solid {rmsd_c};
                      border-radius:8px;padding:16px 20px;">
            <div style="font-size:13px;color:#444;font-weight:500;margin-bottom:6px;">RMSD (A)</div>
            <div style="font-size:36px;font-weight:700;color:{rmsd_c};line-height:1;">{rmsd_str}</div>
            <div style="font-size:12px;color:#666;margin-top:6px;">
              Lower is better &nbsp;·&nbsp; > 3.0 A significant deviation</div>
          </div>
        </div>
        <div style="font-size:12px;color:#666;margin-bottom:4px;">
          Coordinate-only metrics saturate near 1.0 even when function diverges</div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── Signal score cards ────────────────────────────────────────────
        st.markdown("#### FoldShield++ signals")
        if signal_scores and per_signal:
            items = list(per_signal.items())
            for row_start in range(0, len(items), 3):
                row_items = items[row_start:row_start+3]
                cols      = st.columns(len(row_items))
                for col, (display_name, _) in zip(cols, row_items):
                    key   = _DISPLAY_TO_KEY.get(display_name, "")
                    val   = signal_scores.get(key)
                    w     = weights_used.get(key, 0.0)
                    c     = _color(val)
                    is_p2 = "Phase 2" in display_name or "Phase 3" in display_name
                    badge = (' <span style="font-size:10px;background:#e8f4f8;color:#185FA5;'
                             'padding:1px 5px;border-radius:3px;">P2</span>') if is_p2 else ""
                    with col:
                        st.markdown(f"""
                        <div style="border:1px solid #e0e0e0;border-top:3px solid {c};
                                    border-radius:8px;padding:14px 12px;text-align:center;margin-bottom:4px;">
                          <div style="font-size:12px;color:#333;font-weight:500;
                                      margin-bottom:8px;line-height:1.3;">{display_name}{badge}</div>
                          <div style="font-size:30px;font-weight:700;color:{c};line-height:1;">
                                {f"{val:.3f}" if val is not None else "—"}</div>
                          <div style="font-size:11px;color:#666;margin-top:6px;">weight {w:.2f}</div>
                        </div>""", unsafe_allow_html=True)
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            # Interpretation table
            table_rows = ""
            for display_name, interp_text in per_signal.items():
                key   = _DISPLAY_TO_KEY.get(display_name, "")
                val   = signal_scores.get(key)
                w     = weights_used.get(key, 0.0)
                c     = _color(val)
                is_p2 = "Phase 2" in display_name or "Phase 3" in display_name
                badge = ("<span style='font-size:10px;background:#e8f4f8;color:#185FA5;"
                         "padding:1px 5px;border-radius:3px;margin-left:4px;'>P2</span>") if is_p2 else ""
                val_str = f"{val:.3f}" if val is not None else "—"
                table_rows += f"""
                <tr style="border-bottom:1px solid #eee;">
                  <td style="padding:10px 12px;font-size:13px;white-space:nowrap;color:#222;font-weight:500;">
                    {display_name}{badge}</td>
                  <td style="padding:10px 12px;font-size:15px;font-weight:700;color:{c};text-align:center;">
                    {val_str}</td>
                  <td style="padding:10px 12px;font-size:12px;color:#333;">{interp_text}</td>
                  <td style="padding:10px 12px;font-size:12px;color:#555;text-align:center;">{w:.2f}</td>
                </tr>"""
            st.markdown(f"""
            <table style="width:100%;border-collapse:collapse;font-family:inherit;
                          border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
              <thead>
                <tr style="background:#f5f7fa;border-bottom:2px solid #dde1e7;">
                  <th style="padding:10px 12px;text-align:left;font-size:12px;color:#333;">Signal</th>
                  <th style="padding:10px 12px;text-align:center;font-size:12px;color:#333;">Score</th>
                  <th style="padding:10px 12px;text-align:left;font-size:12px;color:#333;">Interpretation</th>
                  <th style="padding:10px 12px;text-align:center;font-size:12px;color:#333;">Weight</th>
                </tr>
              </thead>
              <tbody>{table_rows}</tbody>
            </table>""", unsafe_allow_html=True)

        # ── Combined score + verdict ──────────────────────────────────────
        if fusion:
            st.divider()
            st.markdown("#### Combined score — Fusion Layer v2 (Ridge CV)")
            combined_score = fusion.get("combined_score")
            fusion_mode    = fusion.get("fusion_mode", "—")
            overall        = fusion.get("overall", "—")
            flags          = fusion.get("flags", [])
            c              = _color(combined_score)
            combined_str   = f"{combined_score:.4f}" if combined_score is not None else "—"

            # also show which weight profile was used
            weight_note = ("Phase 2 Ridge CV weights"  if fusion_mode == "phase2"
                           else "CASP17 pre-specified weights" if fusion_mode == "casp17"
                           else fusion_mode)

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:20px;padding:18px 20px;
                        border:1px solid #e0e0e0;border-top:4px solid {c};border-radius:8px;">
              <div style="text-align:center;min-width:90px;">
                <div style="font-size:12px;color:#444;font-weight:500;margin-bottom:4px;">Combined</div>
                <div style="font-size:40px;font-weight:700;color:{c};line-height:1;">{combined_str}</div>
                <div style="font-size:11px;color:#666;margin-top:4px;">{weight_note}</div>
              </div>
              <div style="width:1px;background:#eee;align-self:stretch;"></div>
              <div style="flex:1;">
                <div style="font-size:13px;color:#444;font-weight:500;margin-bottom:4px;">Verdict</div>
                <div style="font-size:16px;font-weight:700;color:{c};">{overall}</div>
              </div>
            </div>""", unsafe_allow_html=True)

            for flag in flags:
                st.warning(f"[FLAG] {flag}")

        # ── Perturbation class ────────────────────────────────────────────
        if p2:
            st.divider()
            st.markdown("#### Perturbation classification — Phase 2")
            gap     = p2.get("gap_score")
            p_class = p2.get("perturbation_class", "—")
            ssef_v  = p2.get("ssef_score")
            loc_v   = p2.get("local_topology_score")
            if gap is not None:
                gap_color = "#2a9d8f" if abs(gap) < 0.15 else ("#f4a261" if abs(gap) < 0.36 else "#e76f51")
            else:
                gap_color = "#999"
            ssef_str = f"{ssef_v:.3f}" if ssef_v is not None else "—"
            loc_str  = f"{loc_v:.3f}"  if loc_v  is not None else "—"
            gap_str  = f"{gap:+.3f}"   if gap     is not None else "—"
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-bottom:10px;">
              <div style="flex:1;border:1px solid #e0e0e0;border-top:3px solid {_color(ssef_v)};
                          border-radius:8px;padding:14px 16px;text-align:center;">
                <div style="font-size:12px;color:#444;font-weight:500;margin-bottom:6px;">SSEF score</div>
                <div style="font-size:28px;font-weight:700;color:{_color(ssef_v)};">{ssef_str}</div>
              </div>
              <div style="flex:1;border:1px solid #e0e0e0;border-top:3px solid {_color(loc_v)};
                          border-radius:8px;padding:14px 16px;text-align:center;">
                <div style="font-size:12px;color:#444;font-weight:500;margin-bottom:6px;">Local topology</div>
                <div style="font-size:28px;font-weight:700;color:{_color(loc_v)};">{loc_str}</div>
              </div>
              <div style="flex:2;border:1px solid {gap_color};border-radius:8px;
                          padding:14px 16px;background:{gap_color}11;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <div>
                    <div style="font-size:12px;color:#444;font-weight:500;margin-bottom:4px;">
                      Gap score (SSEF - local topology)</div>
                    <div style="font-size:32px;font-weight:700;color:{gap_color};">{gap_str}</div>
                  </div>
                  <div style="text-align:right;">
                    <div style="font-size:11px;color:#555;margin-bottom:4px;">Perturbation class</div>
                    <div style="font-size:13px;font-weight:700;padding:6px 12px;
                                background:{gap_color}22;color:{gap_color};border-radius:6px;">{p_class}</div>
                  </div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

            if p2.get("local_topology_unreliable"):
                st.warning("Local topology flagged unreliable — large length mismatch.")
            if p2.get("ssef_note"):
                st.warning(f"SSEF: {p2['ssef_note']}")

        # ── PDF Report ───────────────────────────────────────────────────
        st.divider()
        st.markdown("#### Download Report")
        outdir   = artifacts_dir or summary.get("inputs", {}).get("outdir", "")
        pdf_path = os.path.join(outdir, "similarity_report.pdf") if outdir else ""
        if outdir and not os.path.exists(pdf_path) and summary:
            try:
                from report.report import create_pdf_report as _gen_pdf
                _imgs = []
                for k in ("ref_img", "query_img", "pair_img"):
                    fn = (summary.get("entropy") or {}).get(k, "")
                    if fn:
                        _imgs.append(os.path.join(outdir, fn))
                _gen_pdf(os.path.join(outdir, "summary.json"), _imgs, pdf_path)
            except Exception:
                pass
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="Download PDF report",
                data=pdf_bytes,
                file_name="foldshield_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info("PDF will be generated automatically when the pipeline runs.")


# ---------- VISUALS TAB ----------
with tab_visuals:
    st.subheader("Visuals")
    if not summary:
        st.info("Upload a summary.json or run the pipeline to show images.")
    else:
        outdir    = artifacts_dir or summary.get("inputs", {}).get("outdir", "")
        ref_img   = os.path.join(outdir, "entropy_ref.png")
        query_img = os.path.join(outdir, "entropy_query.png")
        c1, c2   = st.columns(2)
        if os.path.exists(ref_img):   c1.image(ref_img,   caption="Entropy (Ref)",   use_container_width=True)
        if os.path.exists(query_img): c2.image(query_img, caption="Entropy (Query)", use_container_width=True)

        if "tokens_ref" in summary and "tokens_query" in summary:
            ca_ref    = np.array(summary["ca_coords_ref"])
            ca_query  = np.array(summary["ca_coords_query"])
            tokens_ref   = summary["tokens_ref"]
            tokens_query = summary["tokens_query"]
            st.markdown("### UL-DSL Tokenized Backbone (3D)")
            fig_bb = plot_dual_pdb_token_backbones_plotly_separate(
                ca_ref, tokens_ref, ca_query, tokens_query
            )
            st.plotly_chart(fig_bb, use_container_width=True)

        sig      = summary.get("fusion", {}).get("signal_scores", {})
        combined = float(summary.get("combined_similarity") or 0)

        if sig:
            signal_keys   = ["braid", "motif", "topology", "local_topo", "ssef"]
            signal_labels = ["Braid", "Motif", "Global Topo", "Local Topo", "SSEF"]
            values        = [float(sig.get(k, 0) or 0) for k in signal_keys]

            st.markdown("---")
            st.markdown("### Figure 1. Signal Scores")
            bar_colors = ["#4C72B0", "#55A868", "#8172B2", "#C44E52", "#CCB974", "#2d2d2d"]
            fig_bar = go.Figure(go.Bar(
                x=signal_labels + ["Combined"],
                y=values + [combined],
                marker_color=bar_colors,
                text=[f"{v:.3f}" for v in values + [combined]],
                textposition="outside",
            ))
            fig_bar.update_layout(
                yaxis=dict(range=[0, 1.18], title="Score"),
                plot_bgcolor="white", height=400,
                margin=dict(t=30, b=40, l=50, r=20),
                shapes=[
                    dict(type="line", x0=-0.5, x1=5.5, y0=0.75, y1=0.75,
                         line=dict(color="gray", width=1, dash="dash")),
                    dict(type="line", x0=-0.5, x1=5.5, y0=0.50, y1=0.50,
                         line=dict(color="lightgray", width=1, dash="dot")),
                ],
            )
            fig_bar.update_xaxes(showgrid=False)
            fig_bar.update_yaxes(showgrid=True, gridcolor="#eeeeee")
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("---")
            st.markdown("### Figure 2. Signal Profile (Radar)")
            fig_radar = go.Figure(go.Scatterpolar(
                r=values + [values[0]],
                theta=signal_labels + [signal_labels[0]],
                fill="toself",
                fillcolor="rgba(44,114,176,0.18)",
                line=dict(color="#2E75B6", width=2),
                name="Signal profile",
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=[0.75] * (len(signal_labels) + 1),
                theta=signal_labels + [signal_labels[0]],
                mode="lines",
                line=dict(color="gray", width=1, dash="dash"),
                name="0.75 reference",
                showlegend=True,
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                height=450, margin=dict(t=40, b=40, l=60, r=60),
                legend=dict(orientation="h", y=-0.1),
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Phase 2 signal scores not found in summary.")

# ---------- LOG TAB ----------
with tab_log:
    st.subheader("Run Log & Raw Output")
    if log_text:
        st.code(log_text)
    if summary:
        st.caption("Raw summary.json")
        st.json(summary, expanded=False)