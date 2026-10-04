"""Signal registry + static copy. Add or rename a signal here and every card, table and chart follows."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Signal:
    key: str                 # key in fusion["signal_scores"] / ["weights_used"]
    display: str             # name used in fusion["per_signal"]
    label: str               # short chart label
    color: str               # chart colour
    phase: str = ""          # badge text; empty = no badge
    in_charts: bool = True


SIGNALS = (
    Signal("braid",      "Braid similarity",              "Braid",       "#4C72B0"),
    Signal("motif",      "Motif similarity (UL-DSL)",     "Motif",       "#55A868"),
    Signal("topology",   "Global topology",               "Global Topo", "#8172B2"),
    Signal("local_topo", "Local topology (Phase 2)",      "Local Topo",  "#C44E52", phase="P2"),
    Signal("ssef",       "SSEF entropy (Phase 2)",        "SSEF",        "#CCB974", phase="P2"),
    Signal("ph",         "Persistent homology (Phase 3)", "PH",          "#937860", phase="P3", in_charts=False),
)
CHART_SIGNALS = tuple(s for s in SIGNALS if s.in_charts)
_BY_DISPLAY = {s.display: s for s in SIGNALS}


def signal_for(display_name: str) -> Signal:
    """Look up by display name; unknown names still render (grey, no key)."""
    return _BY_DISPLAY.get(display_name) or Signal("", display_name, display_name, "#999999")


FUSION_NOTES = {
    "phase2": "Phase 2 Ridge CV weights",
    "casp17": "CASP17 pre-specified weights",
}
