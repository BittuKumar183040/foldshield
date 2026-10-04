import os
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
    section("Download report")
    pdf_path = os.path.join(outdir, "similarity_report.pdf") if outdir else ""
    if outdir and not os.path.exists(pdf_path):
        _try_generate(summary, outdir, pdf_path)
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF report", f.read(), file_name="foldshield_report.pdf",
                               mime="application/pdf", use_container_width=True)
    else:
        st.info("The PDF report is created when the pipeline runs.")
