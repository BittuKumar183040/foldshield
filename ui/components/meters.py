"""Compact single-value displays (not used by the default tabs; kept from the original app)."""
import streamlit as st
from ui.charts import gauge_fig
from ui.html import esc, render
from ui.theme import score_color


def meter(label, value, *, higher_is_better=True, lo=0.0, hi=1.0) -> None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        st.markdown(f"**{label}:** —")
        return
    norm = min(1.0, max(0.0, (v - lo) / max(1e-9, hi - lo)))
    norm = norm if higher_is_better else 1.0 - norm
    render(f"""
    <div style="margin:4px 0 12px">
      <div class="fs-split" style="font-weight:600"><span>{esc(label)}</span><span>{v:.3f}</span></div>
      <div class="fs-bar"><div style="width:{round(norm * 100)}%;background:{score_color(norm)}"></div></div>
    </div>""")


def gauge(label, value, **kw) -> None:
    try:
        float(value)
    except (TypeError, ValueError):
        st.markdown(f"**{label}:** —")
        return
    st.plotly_chart(gauge_fig(label, value, **kw), use_container_width=True)
