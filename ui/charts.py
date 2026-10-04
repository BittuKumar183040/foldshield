"""Plotly figure builders: pure functions, no Streamlit calls."""
import plotly.graph_objects as go
from ui.config import CHART_SIGNALS
from ui.theme import GOOD, WARN, BAD, BRAND

_CLEAR = "rgba(0,0,0,0)"
_GRID = "rgba(128,128,128,.25)"


def _values(scores: dict) -> list:
    return [float(scores.get(s.key) or 0) for s in CHART_SIGNALS]


def signal_bar_fig(scores: dict, combined: float) -> go.Figure:
    labels = [s.label for s in CHART_SIGNALS] + ["Combined"]
    values = _values(scores) + [combined]
    colors = [s.color for s in CHART_SIGNALS] + ["#6c757d"]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors,
                           text=[f"{v:.3f}" for v in values], textposition="outside"))
    fig.add_hline(y=0.75, line_dash="dash", line_color="gray", line_width=1)
    fig.add_hline(y=0.50, line_dash="dot", line_color="lightgray", line_width=1)
    fig.update_layout(
        yaxis=dict(range=[0, 1.18], title="Score", gridcolor=_GRID),
        plot_bgcolor=_CLEAR, paper_bgcolor=_CLEAR, showlegend=False,
        height=380, margin=dict(t=20, b=40, l=50, r=20),
    )
    fig.update_xaxes(showgrid=False)
    return fig


def signal_radar_fig(scores: dict) -> go.Figure:
    labels = [s.label for s in CHART_SIGNALS]
    values = _values(scores)
    closed_labels = labels + labels[:1]
    fig = go.Figure(go.Scatterpolar(
        r=values + values[:1], theta=closed_labels, fill="toself",
        fillcolor="rgba(44,114,176,0.18)", line=dict(color=BRAND, width=2), name="Signal profile"))
    fig.add_trace(go.Scatterpolar(
        r=[0.75] * len(closed_labels), theta=closed_labels, mode="lines",
        line=dict(color="gray", width=1, dash="dash"), name="0.75 reference"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        paper_bgcolor=_CLEAR, height=380, margin=dict(t=30, b=40, l=60, r=60),
        legend=dict(orientation="h", y=-0.1),
    )
    return fig


def gauge_fig(label, value, *, vmin=0.0, vmax=1.0, invert=False, suffix="") -> go.Figure:
    lo = vmin + 0.33 * (vmax - vmin)
    hi = vmin + 0.66 * (vmax - vmin)
    steps = [{"range": [vmin, lo], "color": BAD},
             {"range": [lo, hi], "color": WARN},
             {"range": [hi, vmax], "color": GOOD}]
    if invert:
        steps = [{**s, "color": c} for s, c in zip(steps, (GOOD, WARN, BAD))]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=float(value), title={"text": label},
        number={"suffix": suffix, "valueformat": ".3f"},
        gauge={"axis": {"range": [vmin, vmax]}, "bar": {"color": "#264653"}, "steps": steps}))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor=_CLEAR)
    return fig
