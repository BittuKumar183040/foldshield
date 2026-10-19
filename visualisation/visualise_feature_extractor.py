"""
feature_visualization.py
------------------------

Visual diagnostics for UL-DSL feature extraction.

Plots:
1. Curvature vs residue index (with DSSP overlay)
2. Torsion vs residue index (with DSSP overlay)
3. CA–CA distance vs residue index
4. 3D CA backbone colored by feature value

This is a SANITY + INTUITION tool.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
# from visualisation.visualise_feature_extractor import FeatureExtractor
from matplotlib.colors import ListedColormap
import plotly.graph_objects as go
# -------------------------------
# DSSP color map
# -------------------------------

DSSP_COLORS = {
    "H": "#e63946",  # helix - red
    "E": "#457b9d",  # beta  - blue
    "T": "#f4a261",  # turn  - orange
    "L": "#999999",  # loop  - gray
}


# -------------------------------
# Helper: background DSSP shading
# -------------------------------
import matplotlib.pyplot as plt
import numpy as np

def plot_dssp_strip(dssp_labels):
    mapping = {"H": 0, "E": 1, "T": 2, "L": 3}
    colors = ["red", "blue", "green", "gray"]
    values = [mapping[x] for x in dssp_labels]

    plt.figure(figsize=(12, 1.5))
    plt.imshow([values], aspect="auto", cmap=plt.cm.get_cmap("tab10", 4))
    plt.yticks([])
    plt.xticks(range(0, len(values), 5))
    plt.colorbar(
        ticks=[0,1,2,3],
        label="DSSP",
        format=lambda x, _: ["H","E","T","L"][int(x)]
    )
    plt.title("DSSP Secondary Structure Along Backbone")
    plt.tight_layout()
    plt.show()

def overlay_dssp(ax, ss_labels):
    for i, ss in enumerate(ss_labels):
        ax.axvspan(i - 0.5, i + 0.5,
                   color=DSSP_COLORS.get(ss, "#cccccc"),
                   alpha=0.15)


# -------------------------------
# 1D Feature plots
# -------------------------------

def plot_feature(feature, title, ylabel, ss_labels=None):
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.plot(feature, linewidth=1.8)
    ax.set_title(title)
    ax.set_xlabel("Residue index")
    ax.set_ylabel(ylabel)

    if ss_labels is not None:
        overlay_dssp(ax, ss_labels)

    plt.tight_layout()
    plt.show()


# -------------------------------
# 3D Backbone visualization
# -------------------------------

def plot_3d_backbone(ca_coords, feature, title):
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")

    sc = ax.scatter(
        ca_coords[:, 0],
        ca_coords[:, 1],
        ca_coords[:, 2],
        c=feature,
        cmap="viridis",
        s=18
    )

    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    plt.colorbar(sc, ax=ax, label="Feature value")
    plt.tight_layout()
    plt.show()
    
    
# --------------------------------------------------
# Token color map (stable & interpretable)
# --------------------------------------------------

TOKEN_COLORS = {
    "H_alpha": "#e41a1c",
    "H_310": "#fb8072",
    "H_pi": "#b2182b",
    "B_parallel": "#377eb8",
    "B_antiparallel": "#4daf4a",
    "B_isolated": "#80b1d3",
    "B_strand": "#377eb8",
    "T_tight": "#984ea3",
    "T_medium": "#c994c7",
    "T_wide": "#decbe4",
    "L_short": "#fdb462",
    "L_medium": "#ffeda0",
    "L_long": "#fee391",
    "C_coil": "#bdbdbd",
}


# --------------------------------------------------
# 1. Feature vs residue index
# --------------------------------------------------

def plot_residue_vs_index_feature(feature, title, ylabel):
    x = np.arange(len(feature))
    plt.figure(figsize=(10, 3))
    plt.plot(x, feature, lw=1.5)
    plt.xlabel("Residue index")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.show()


# --------------------------------------------------
# 2. Token strip visualization
# --------------------------------------------------

def plot_token_strip(tokens):
    unique_tokens = list(dict.fromkeys(tokens))
    token_to_int = {t: i for i, t in enumerate(unique_tokens)}
    ints = [token_to_int[t] for t in tokens]

    cmap = ListedColormap([TOKEN_COLORS.get(t, "#cccccc") for t in unique_tokens])

    plt.figure(figsize=(12, 1.8))
    plt.imshow([ints], aspect="auto", cmap=cmap)
    plt.yticks([])
    plt.xlabel("Residue index")
    plt.title("UL-DSL Token Strip")

    # Legend
    handles = [
        plt.Line2D([0], [0], color=TOKEN_COLORS.get(t, "#ccc"), lw=6)
        for t in unique_tokens
    ]
    plt.legend(handles, unique_tokens, bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()
    plt.show()


# --------------------------------------------------
# 3. Curvature + token overlay
# --------------------------------------------------

def plot_curvature_with_tokens(curvature, tokens):
    x = np.arange(len(curvature))

    plt.figure(figsize=(12, 4))
    plt.plot(x, curvature, color="black", lw=1.2, label="Curvature κ")

    for i, tok in enumerate(tokens):
        plt.axvspan(
            i - 0.5,
            i + 0.5,
            color=TOKEN_COLORS.get(tok, "#eeeeee"),
            alpha=0.25,
        )

    plt.xlabel("Residue index")
    plt.ylabel("Curvature κ")
    plt.title("Curvature with UL-DSL Token Overlay")
    plt.legend()
    plt.tight_layout()
    plt.show()


# --------------------------------------------------
# 4. 3D backbone colored by token
# --------------------------------------------------

def plot_3d_backbone_with_token(ca_coords, tokens):
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")

    for i in range(len(ca_coords) - 1):
        x = ca_coords[i:i+2, 0]
        y = ca_coords[i:i+2, 1]
        z = ca_coords[i:i+2, 2]
        color = TOKEN_COLORS.get(tokens[i], "#cccccc")
        ax.plot(x, y, z, color=color, lw=2)

    ax.set_title("3D Backbone Colored by UL-DSL Tokens")
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()
    
def plot_3d_backbone_with_tokens(ax, ca_coords, tokens, title=""):
    for i in range(len(ca_coords) - 1):
        x = ca_coords[i:i+2, 0]
        y = ca_coords[i:i+2, 1]
        z = ca_coords[i:i+2, 2]
        color = TOKEN_COLORS.get(tokens[i], "#cccccc")
        ax.plot(x, y, z, color=color, lw=2)

    ax.set_title(title)
    ax.set_axis_off()
    
from plotly.subplots import make_subplots

def plot_dual_pdb_token_backbones_plotly_separate(
    ca_ref, tokens_ref,
    ca_query, tokens_query,
    title_ref="Reference UL-DSL Tokens",
    title_query="Query UL-DSL Tokens",
    view_mode="Side-by-side",
    focus_index=None,
):
    """Render two JSON-sourced C-alpha traces side by side or as a fitted overlay."""
    ca_ref = np.asarray(ca_ref, dtype=float)
    ca_query = np.asarray(ca_query, dtype=float)
    tokens_ref, tokens_query = list(tokens_ref), list(tokens_query)
    overlay = view_mode == "Superimposed" and len(ca_ref) == len(ca_query) and len(ca_ref) > 1

    if overlay:
        ref_center = ca_ref.mean(axis=0)
        query_center = ca_query.mean(axis=0)
        ref_centered = ca_ref - ref_center
        query_centered = ca_query - query_center
        u, _, vt = np.linalg.svd(query_centered.T @ ref_centered)
        rotation = u @ vt
        if np.linalg.det(rotation) < 0:
            u[:, -1] *= -1
            rotation = u @ vt
        ca_query = query_centered @ rotation + ref_center
        fig = make_subplots(rows=1, cols=1, specs=[[{"type": "scene"}]])
        scenes = [(ca_ref, tokens_ref, 1, "Reference", "#168f91"),
                  (ca_query, tokens_query, 1, "Query", "#e4775d")]
        # Keep the overlay legend concise: model identity is encoded by color.
        for model_name, color in (("Reference", "#168f91"), ("Query", "#e4775d")):
            fig.add_trace(go.Scatter3d(x=[None, None], y=[None, None], z=[None, None],
                                       mode="lines", name=model_name,
                                       line=dict(color=color, width=7), hoverinfo="skip"))
    else:
        fig = make_subplots(rows=1, cols=2, specs=[[{"type": "scene"}, {"type": "scene"}]],
                            subplot_titles=[title_ref, title_query])
        scenes = [(ca_ref, tokens_ref, 1, "Reference", None),
                  (ca_query, tokens_query, 2, "Query", None)]

    for coords, tokens, scene_id, model_name, color_override in scenes:
        # Combine disjoint segments of each token into one trace instead of making
        # one Plotly trace per residue pair. This cuts hundreds of traces to a handful.
        token_segments = {}
        for i in range(max(0, min(len(coords) - 1, len(tokens)))):
            token = str(tokens[i])
            bucket = token_segments.setdefault(token, ([], [], [], []))
            xs, ys, zs, hover = bucket
            text = f"{model_name} · residue {i + 1} · {token}"
            xs.extend((coords[i, 0], coords[i + 1, 0], None))
            ys.extend((coords[i, 1], coords[i + 1, 1], None))
            zs.extend((coords[i, 2], coords[i + 1, 2], None))
            hover.extend((text, text, None))

        for token, (xs, ys, zs, hover) in token_segments.items():
            color = color_override or TOKEN_COLORS.get(token, "#aab4bd")
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs, mode="lines", line=dict(color=color, width=6),
                text=hover, hovertemplate="%{text}<extra></extra>",
                name=token, legendgroup=token,
                showlegend=not overlay and model_name == "Reference",
            ), row=1, col=scene_id)

        if focus_index is not None and 0 <= focus_index < len(coords):
            token = tokens[focus_index] if focus_index < len(tokens) else "Unknown"
            fig.add_trace(go.Scatter3d(
                x=[coords[focus_index, 0]], y=[coords[focus_index, 1]], z=[coords[focus_index, 2]],
                mode="markers+text", text=[str(focus_index + 1)], textposition="top center",
                marker=dict(size=7, color="#f3ad34", line=dict(color="white", width=2)),
                name=f"{model_name} focus", showlegend=False,
                hovertemplate=f"{model_name} · residue {focus_index + 1} · {token}<extra></extra>",
            ), row=1, col=scene_id)

    fig.update_layout(
        height=650, autosize=True, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#294655"), legend_title_text="UL-DSL Tokens" if not overlay else "Model",
        margin=dict(l=0, r=0, t=58 if not overlay else 24, b=0),
        uirevision=f"fs-backbone-{view_mode}",
        scene=dict(aspectmode="data"),
        scene2=dict(aspectmode="data"),
    )
    fig.update_scenes(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False))
    return fig
