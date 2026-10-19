import os
from pathlib import Path
import streamlit as st
from ui.components.cards import section


def _try_generate(summary: dict, outdir: str, pdf_path: str) -> None:
    try:
        from report.report import create_pdf_report
        imgs = []
        for k in ("ref_img", "query_img", "pair_img"):
            fn = (summary.get("entropy") or {}).get(k, "")
            if fn:
                imgs.append(os.path.join(outdir, fn))
        create_pdf_report(os.path.join(outdir, "summary.json"), imgs, pdf_path)
    except Exception as e:
        st.caption(f"Could not generate the PDF report: {e}")


def report_download(summary: dict, outdir: str) -> None:
    section("Report preview", "Use the PDF viewer controls to print or save a copy.")
    pdf_path = os.path.join(outdir, "similarity_report.pdf") if outdir else ""
    if outdir and not os.path.exists(pdf_path):
        _try_generate(summary, outdir, pdf_path)
    if pdf_path and os.path.exists(pdf_path):
        st.markdown(
            """<style>
            [data-testid="stDialog"]:has(.st-key-fs-report-preview) {
              align-items: flex-start !important;
              padding-block: 0 !important;
              overflow: hidden !important;
              overscroll-behavior: none;
            }
            [data-testid="stDialog"]:has(.st-key-fs-report-preview) > div {
              width: 96vw !important;
              max-width: 1400px !important;
              max-height: calc(100dvh - 1rem) !important;
              margin-block: 0 !important;
              overflow: hidden !important;
              display: flex !important;
              flex-direction: column !important;
            }
            .st-key-fs-report-preview {
              height: clamp(180px, calc(100dvh - 17rem), 640px) !important;
              min-height: 180px !important;
              max-height: clamp(180px, calc(100dvh - 17rem), 640px) !important;
              flex: 0 1 auto !important;
              overflow: hidden !important;
            }
            .st-key-fs-report-preview iframe {
              height: 100% !important;
              max-height: 100% !important;
              overflow: auto !important;
            }
            </style>""",
            unsafe_allow_html=True,
        )
        with st.container(key="fs-report-preview", width="stretch"):
            st.pdf(Path(pdf_path), height=700, alt="FoldShield PDF report preview")
        with open(pdf_path, "rb") as report_file:
            st.download_button(
                "Download PDF report",
                report_file.read(),
                file_name="foldshield_report.pdf",
                mime="application/pdf",
                icon=":material/download:",
                width="stretch",
            )
    else:
        st.info("The PDF report is created when the pipeline runs.")
