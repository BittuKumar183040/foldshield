# visualizer_pair.py
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist
import matplotlib
# use non-interactive backend so saving works on servers
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, Optional,Sequence,Tuple
import textwrap
import json
import matplotlib.pyplot as plt
# --- small util: kabsch superpose two Nx3 arrays (returns rotated coords_b and RMSD per residue) ---
def kabsch_superpose(A, B):
    # A, B shapes (N,3); returns B_aligned, per_residue_distances, rmsd
    assert A.shape == B.shape
    # center
    a0 = A.mean(axis=0); b0 = B.mean(axis=0)
    A_c = A - a0; B_c = B - b0
    # covariance
    H = B_c.T @ A_c
    U, S, Vt = np.linalg.svd(H)
    d = np.linalg.det(U @ Vt)
    M = np.diag([1,1,np.sign(d)])
    Rmat = U @ M @ Vt
    B_aligned = (B_c @ Rmat.T) + a0
    dists = np.linalg.norm(A - B_aligned, axis=1)
    rmsd = np.sqrt((dists**2).mean())
    return B_aligned, dists, rmsd

# --- simple helper to draw braid word as text with highlights ---
def draw_braid_text(ax, gensA, gensB, max_len=80):
    # gens as list of strings or tuples; convert to str
    sA = " ".join(map(str, gensA[:max_len]))
    sB = " ".join(map(str, gensB[:max_len]))
    ax.text(0.01, 0.7, "Ref braid:", fontsize=8, family="monospace")
    ax.text(0.01, 0.6, sA, fontsize=7, family="monospace")
    ax.text(0.01, 0.35, "Query braid:", fontsize=8, family="monospace")
    ax.text(0.01, 0.25, sB, fontsize=7, family="monospace")
    ax.axis('off')

def _safe_array(a):
    if a is None:
        return np.zeros((0,2))
    arr = np.array(a)
    if arr.size == 0:
        return arr.reshape((0,2))
    if arr.ndim == 1:
        # single point
        if arr.size == 2:
            return arr.reshape((1,2))
        return arr.reshape((-1,2))
    return arr

def composite_pair_report(braid_ref: Dict[str,Any],
                          braid_query: Dict[str,Any],
                          out_path: str,
                          title: Optional[str] = None,
                          show_labels: bool = False,
                          max_word_len: int = 120):
    """
    Create a composite PNG summarizing two braids / PDB-derived info.
    Writes file to out_path and returns out_path on success.
    braid_* expected keys:
        - 'proj2d' (list of [x,y])  OR None
        - 'labels' (list of residue labels) OR None
        - 'braid_word_simplified' (list of strings) OR []
        - 'entropy_tensor' (2D array) OR None
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # sanitize inputs
    p_ref = _safe_array(braid_ref.get("proj2d"))
    p_qry = _safe_array(braid_query.get("proj2d"))
    labels_ref = braid_ref.get("labels") or []
    labels_qry = braid_query.get("labels") or []
    word_ref = braid_ref.get("braid_word_simplified") or braid_ref.get("braid_word") or []
    word_qry = braid_query.get("braid_word_simplified") or braid_query.get("braid_word") or []
    ent_ref = np.array(braid_ref.get("entropy_tensor") or [])
    ent_qry = np.array(braid_query.get("entropy_tensor") or [])

    # Basic validation
    if p_ref.size == 0 and p_qry.size == 0 and ent_ref.size == 0 and ent_qry.size == 0:
        raise ValueError("No projection or entropy data found in either braid_ref or braid_query.")

    # Create figure (3 panels horizontally)
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    ax_proj, ax_words, ax_heat = axes

    # Left: projections scatter (both overlaid)
    def _plot_proj(ax, pts, labels, name, color, alpha=0.8):
        if pts.size == 0:
            ax.text(0.5, 0.5, f"No projection for\n{name}", ha='center', va='center', fontsize=10, transform=ax.transAxes)
            return
        pts = np.array(pts)
        ax.scatter(pts[:,0], pts[:,1], s=12, marker='o', label=name, alpha=alpha)
        if show_labels and labels:
            for i, lbl in enumerate(labels):
                if i < pts.shape[0]:
                    ax.text(pts[i,0], pts[i,1], str(lbl), fontsize=6)
    _plot_proj(ax_proj, p_ref, labels_ref, "ref", "C0")
    _plot_proj(ax_proj, p_qry, labels_qry, "query", "C1", alpha=0.6)
    ax_proj.set_title("Projected backbone (2D)")
    ax_proj.legend(loc='upper right', fontsize=8)
    ax_proj.axison = True

    # Middle: braid words summary
    def _word_to_text(word_list):
        if not word_list:
            return "(no braid word)"
        joined = " ".join(word_list)
        if len(joined) > max_word_len:
            # wrap long text to multiple lines
            return "\n".join(textwrap.wrap(joined, width=80))
        return joined

    ref_txt = "REF braid (first 120 chars):\n\n" + _word_to_text(word_ref)
    qry_txt = "QUERY braid (first 120 chars):\n\n" + _word_to_text(word_qry)
    combined = ref_txt + "\n\n" + ("-"*40) + "\n\n" + qry_txt
    ax_words.text(0.01, 0.99, combined, va='top', ha='left', fontsize=8, family='monospace')
    ax_words.axis('off')
    ax_words.set_title("Symbolic braid words")

    # Right: show entropy heatmaps (stacked vertically if both exist)
    if ent_ref.size == 0 and ent_qry.size == 0:
        ax_heat.text(0.5, 0.5, "No entropy tensors", ha='center', va='center')
        ax_heat.axis('off')
    else:
        # if both present, create sub-axes vertically
        if ent_ref.size != 0 and ent_qry.size != 0:
            from mpl_toolkits.axes_grid1 import make_axes_locatable
            ax_top = ax_heat
            ax_bottom = fig.add_axes([0.77, 0.11, 0.2, 0.35])  # manual placement
            im1 = ax_top.imshow(ent_ref, origin='lower', aspect='auto')
            ax_top.set_title("Ref entropy")
            ax_top.axis('off')
            im2 = ax_bottom.imshow(ent_qry, origin='lower', aspect='auto')
            ax_bottom.set_title("Query entropy")
            ax_bottom.axis('off')
            # colorbar for first image
            divider = make_axes_locatable(ax_top)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            fig.colorbar(im1, cax=cax)
        else:
            # just one tensor, plot it
            ent = ent_ref if ent_ref.size != 0 else ent_qry
            im = ax_heat.imshow(ent, origin='lower', aspect='auto')
            ax_heat.set_title("Entropy tensor")
            ax_heat.axis('off')
            fig.colorbar(im, ax=ax_heat, fraction=0.046, pad=0.04)

    # Title
    if title:
        fig.suptitle(title)
    else:
        fig.suptitle("Pair Report")

    # save
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def assert_entropy_array(arr):
    """Enforce returned type from generator. Raise if wrong."""
    if not isinstance(arr, np.ndarray):
        raise TypeError("Entropy tensor must be a numpy.ndarray, got: %s" % type(arr))
    if arr.ndim != 2:
        raise ValueError("Entropy tensor must be 2D (H,W). Got shape: %s" % (arr.shape,))
    return True


def _to_json_safe(obj: Any):
    """
    Recursively convert numpy types (ndarray, scalars) and other non-json
    types into json-serializable python builtins.
    """
    # numpy arrays -> lists
    if isinstance(obj, np.ndarray):
        # convert to Python nested lists (and cast numpy scalar types to python)
        return _to_json_safe(obj.tolist())

    # numpy/np scalar types
    if isinstance(obj, (np.generic,)):
        try:
            return obj.item()
        except Exception:
            return float(obj)

    # common containers
    if isinstance(obj, dict):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_json_safe(v) for v in obj]

    # basic python types OK for json
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    # fallback: try str()
    return str(obj)


def save_entropy_json(entropy_map: np.ndarray, meta: Dict[str, Any], out_path: str) -> Tuple[str, str]:
    """
    Save raw entropy numpy array (.npy) and metadata (.json).
    - entropy_map: numpy 2D array
    - meta: dictionary returned by generate_entropy_tensor
    - out_path: path for json (will create .npy alongside)
    Returns: (npy_path, json_path)
    """
    if not isinstance(entropy_map, np.ndarray):
        entropy_map = np.asarray(entropy_map, dtype=float)

    # ensure directory
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Save raw numpy array next to JSON
    npy_path = out_path.replace(".json", ".npy")
    # Use allow_pickle=False for safety
    np.save(npy_path, entropy_map, allow_pickle=False)

    # Prepare JSON-friendly meta
    meta_copy = dict(meta) if isinstance(meta, dict) else {"meta": str(meta)}
    meta_copy["npy_path"] = os.path.basename(npy_path)
    meta_copy["shape"] = list(entropy_map.shape)
    # safe numeric min/max (handles NaN)
    try:
        meta_copy["min"] = float(np.nanmin(entropy_map))
        meta_copy["max"] = float(np.nanmax(entropy_map))
    except Exception:
        meta_copy["min"] = None
        meta_copy["max"] = None

    # Convert everything to JSON-safe types
    safe_meta = _to_json_safe(meta_copy)

    # Write JSON
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(safe_meta, fh, indent=2)

    return npy_path, out_path


def load_entropy_json(inpath: str) -> np.ndarray:
    with open(inpath, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    shp = tuple(payload["shape"])
    data = np.array(payload["data"], dtype=float).reshape(shp)
    return data


def resample_2d_to_shape(arr: np.ndarray, target_shape: tuple) -> np.ndarray:
    """
    Resample a 2D numpy array `arr` to `target_shape` (rows, cols).
    - nearest-neighbor mapping .
    """
    if not isinstance(arr, np.ndarray):
        arr = np.asarray(arr, dtype=float)

    target_shape = tuple(map(int, target_shape))
    if arr.shape == target_shape:
        return arr.copy()


    src_r, src_c = arr.shape
    dst_r, dst_c = target_shape
    # compute source indices for each destination pixel
    row_idx = (np.linspace(0, src_r - 1, dst_r)).round().astype(int)
    col_idx = (np.linspace(0, src_c - 1, dst_c)).round().astype(int)
    # use broadcasting to build grid
    res = arr[np.ix_(row_idx, col_idx)]
    return res


def plot_entropy_surface(entropy: np.ndarray, out_path: str, title="Entropy", vmin=None, vmax=None):
    assert_entropy_array(entropy)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.figure(figsize=(6, 6))
    im = plt.imshow(entropy, origin="lower", cmap="inferno", vmin=vmin, vmax=vmax)
    plt.colorbar(im, label="Entropy")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_entropy_pair_side_by_side(ent_ref: np.ndarray, ent_query: np.ndarray, out_path: str, titles=("Ref", "Query")):
    # resample copies to same shape for side-by-side
    assert_entropy_array(ent_ref); assert_entropy_array(ent_query)
    # choose the larger shape (preserve resolution) as target
    Ht = max(ent_ref.shape[0], ent_query.shape[0])
    Wt = max(ent_ref.shape[1], ent_query.shape[1])
    ref_r = resample_2d_to_shape(ent_ref, (Ht, Wt))
    query_r = resample_2d_to_shape(ent_query, (Ht, Wt))

    vmin = min(np.nanmin(ref_r), np.nanmin(query_r))
    vmax = max(np.nanmax(ref_r), np.nanmax(query_r))
    if vmax == vmin:
        vmax = vmin + 1e-6

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))
    axs[0].imshow(ref_r, origin="lower", cmap="inferno", vmin=vmin, vmax=vmax)
    axs[0].set_title(titles[0])
    axs[1].imshow(query_r, origin="lower", cmap="inferno", vmin=vmin, vmax=vmax)
    axs[1].set_title(titles[1])
    plt.colorbar(axs[1].images[0], ax=axs.ravel().tolist(), shrink=0.6)
    # plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path