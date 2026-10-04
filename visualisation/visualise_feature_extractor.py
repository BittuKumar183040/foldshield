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
    title_query="Query UL-DSL Tokens"
):
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "scene"}, {"type": "scene"}]],
        subplot_titles=[title_ref, title_query]
    )

    def add_backbone(fig, ca_coords, tokens, scene_id, show_legend_tokens=True):
        seen_tokens = set()

        for i in range(len(ca_coords) - 1):
            token = tokens[i]
            color = TOKEN_COLORS.get(token, "#cccccc")

            show_legend = False
            if show_legend_tokens and token not in seen_tokens:
                show_legend = True
                seen_tokens.add(token)

            fig.add_trace(
                go.Scatter3d(
                    x=[ca_coords[i, 0], ca_coords[i+1, 0]],
                    y=[ca_coords[i, 1], ca_coords[i+1, 1]],
                    z=[ca_coords[i, 2], ca_coords[i+1, 2]],
                    mode="lines",
                    line=dict(color=color, width=6),
                    name=token,
                    legendgroup=token,
                    showlegend=show_legend,
                    hovertemplate=(
                        f"Residue: {i}<br>"
                        f"Token: {token}<extra></extra>"
                    )
                ),
                row=1,
                col=scene_id
            )

    add_backbone(fig, ca_ref, tokens_ref, scene_id=1, show_legend_tokens=True)
    add_backbone(fig, ca_query, tokens_query, scene_id=2, show_legend_tokens=False)

    fig.update_layout(
        height=650,
        legend_title_text="UL-DSL Tokens",
        margin=dict(l=0, r=0, t=50, b=0)
    )

    fig.update_scenes(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        zaxis=dict(visible=False)
    )

    return fig