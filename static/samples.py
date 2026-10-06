"""Sample comparisons shown as cards on the Home page.

Each entry:
    id     folder name, also the dict key
    title  heading shown on the card
    desc   short description (the card clamps it to 3 lines)
    tags   small pills shown under the title
    path   result folder, relative to the project root. It holds:
               thumbnail.png   card image
               summary.json    scores (read for the score line and "Open in analyzer")
               <REF>.pdb       reference structure, e.g. 1A3N.pdb
               <QUERY>.pdb     query structure,     e.g. 1A00.pdb

Add a comparison with  "<id>": _entry(<id>, desc, tags)  or  _generic(<id>)  inside SAMPLES.
"""


def _entry(pair: str, desc: str, tags: list[str]) -> dict:
    return {
        "id": pair,
        "title": pair,
        "desc": desc,
        "tags": tags,
        "path": f"results/{pair}",
    }


_GENERIC = "Sample comparison of PDB entries {a} and {b}. Open it in the analyzer to see the full similarity breakdown."


def _generic(pair: str) -> dict:
    a, b = pair.removeprefix("ca_").split("_vs_")
    return _entry(pair, _GENERIC.format(a=a, b=b), ["benchmark"])


SAMPLES: dict[str, dict] = {
    # --- same protein, different state or experiment ----------------------------------
    "ca_1AKE_vs_4AKE": _entry(
        "ca_1AKE_vs_4AKE",
        "Adenylate kinase in its closed (1AKE) and open (4AKE) forms. A large hinge motion "
        "moves the lid domains while the fold stays the same, a classic test for conformational change.",
        ["same-protein", "conformational-change"],
    ),
    "ca_1UBQ_vs_1UBI": _entry(
        "ca_1UBQ_vs_1UBI",
        "Two ubiquitin entries. The structures should agree closely, so this pair checks that "
        "the scores stay high when nothing meaningful has changed.",
        ["same-protein", "expected-similar"],
    ),
    "ca_1HHO_vs_2HHO": _entry(
        "ca_1HHO_vs_2HHO",
        "Two oxyhemoglobin entries. Same protein family and fold, with only small differences "
        "between the models.",
        ["same-protein", "expected-similar"],
    ),
    "ca_1TIM_vs_4TIM": _entry(
        "ca_1TIM_vs_4TIM",
        "Two triosephosphate isomerase (TIM) entries. Both share the TIM-barrel fold, so the "
        "scores should reflect a close structural match.",
        ["same-family", "expected-similar"],
    ),
    "ca_1T15_vs_1JNX": _entry(
        "ca_1T15_vs_1JNX",
        "Two BRCA1 BRCT-domain structures. Same domain solved in different complexes, which tests "
        "sensitivity to small local differences.",
        ["same-family", "expected-similar"],
    ),
    # --- related proteins, different domains ------------------------------------------
    "ca_1JM7_vs_1JNX": _entry(
        "ca_1JM7_vs_1JNX",
        "Two different regions of BRCA1: the RING domain complex (1JM7) and the BRCT domains (1JNX). "
        "Related protein, different folds.",
        ["same-protein", "different-domains"],
    ),
    # --- unrelated folds (expected to score low) --------------------------------------
    "ca_1UBQ_vs_1CRN": _entry(
        "ca_1UBQ_vs_1CRN",
        "Ubiquitin against crambin, two small proteins with different folds. A negative control: "
        "the similarity score should stay low.",
        ["unrelated-folds", "negative-control"],
    ),
    "ca_1UBQ_vs_1HHO": _entry(
        "ca_1UBQ_vs_1HHO",
        "Ubiquitin against hemoglobin, with no shared fold. A negative control that should "
        "score as dissimilar.",
        ["unrelated-folds", "negative-control"],
    ),
    "ca_1TIM_vs_1HHO": _entry(
        "ca_1TIM_vs_1HHO",
        "A TIM barrel against the all-helical globin fold of hemoglobin. Different architectures, "
        "so the comparison should come out dissimilar.",
        ["unrelated-folds", "negative-control"],
    ),
    "ca_1TIM_vs_2RH1": _entry(
        "ca_1TIM_vs_2RH1",
        "A TIM barrel against the beta-2 adrenergic receptor, a membrane GPCR. Very different "
        "topologies, used as a negative control.",
        ["unrelated-folds", "negative-control"],
    ),
    # --- pairs to describe once you have looked at the results ------------------------
    "ca_1A3N_vs_1A00": _generic("ca_1A3N_vs_1A00"),
    "ca_1CRN_vs_1CSH": _generic("ca_1CRN_vs_1CSH"),
    "ca_1CRN_vs_4OBE": _generic("ca_1CRN_vs_4OBE"),
    "ca_1IYJ_vs_1T15": _generic("ca_1IYJ_vs_1T15"),
    "ca_1J9O_vs_2JP1": _generic("ca_1J9O_vs_2JP1"),
    "ca_1JM7_vs_4OBE": _generic("ca_1JM7_vs_4OBE"),
    "ca_1QLP_vs_1H8H": _generic("ca_1QLP_vs_1H8H"),
    "ca_1S2H_vs_2V64": _generic("ca_1S2H_vs_2V64"),
    "ca_1UBQ_vs_1J85": _generic("ca_1UBQ_vs_1J85"),
}


# =============================================================================
# Structures offered in the Analyze page's Reference / Query pickers.
# Each side has its own list. Entry fields:
#     id       PDB code, also the file name:  <PDB_DIR>/<id>.pdb
#     label    text shown in the list and on the chip
#     icon     emoji (or any short text) shown in front of the label
#     path     where the .pdb file lives, relative to the project root
#     details  free-form {name: value}; every pair is shown under the label,
#              so add more keys here whenever you want more info on the list
# If <path> does not exist, the picker also looks for results/*/<id>.pdb.
# =============================================================================
PDB_DIR = "pdb files"


def _pdb(id: str, label: str = None, recommendation: list = None, protein: str = "", icon: str = "🧬", **extra: str) -> dict:
    details = {"Protein": protein} if protein else {}
    details.update(extra)
    return {
        "id": id,
        "label": label,
        "recommendation": recommendation or [""],
        "icon": icon,
        "path": f"{PDB_DIR}/{id}.pdb",
        "details": details,
    }

def _table(*entries: dict) -> dict[str, dict]:
    return {e["id"]: e for e in entries}

PDBs: dict[str, dict] = _table(
    _pdb( id="1A3N", label="Hemoglobin", recommendation=["1A00", "1HHO"], protein="Deoxy human hemoglobin" ),
    _pdb( id="1A00", label="Hemoglobin mutant", recommendation=["1A3N", "1HHO"], protein="Human hemoglobin beta mutant" ),
    _pdb( id="1HHO", label="Oxyhemoglobin", recommendation=["1A3N", "1A00"], protein="Human oxyhemoglobin" ),
    _pdb( id="2HHO", label="Insulin mutant", recommendation=["1A3N"], protein="Human insulin mutant" ),
    _pdb( id="1AKE", label="Adenylate kinase (closed)", recommendation=["4AKE"], protein="Adenylate kinase" ),
    _pdb( id="4AKE", label="Adenylate kinase (open)", recommendation=["1AKE"], protein="Adenylate kinase" ),
    _pdb( id="1CRN", label="Crambin", recommendation=["1UBQ"], protein="Crambin" ),
    _pdb( id="1IYJ", label="BRCA2–DSS1 complex", recommendation=["1JM7", "1JNX", "1T15"], protein="BRCA2–DSS1 complex" ),
    _pdb( id="1JM7", label="BRCA1/BARD1 RING domains", recommendation=["1JNX", "1T15", "1IYJ"], protein="BRCA1/BARD1 RING-domain heterodimer" ),
    _pdb( id="1JNX", label="BRCA1 BRCT domains", recommendation=["1T15", "1JM7", "1IYJ"], protein="BRCA1 BRCT repeat region" ),
    _pdb( id="1T15", label="BRCA1 BRCT–BACH1 complex", recommendation=["1JNX", "1JM7", "1IYJ"], protein="BRCA1 BRCT domains with BACH1 peptide" ),
    _pdb( id="1J9O", label="Lymphotactin", recommendation=["2JP1"], protein="Human lymphotactin (XCL1)" ),
    _pdb( id="2JP1", label="Lymphotactin (alternative)", recommendation=["1J9O"], protein="Human lymphotactin (XCL1)" ),
    _pdb( id="1S2H", label="Mad2 spindle checkpoint protein", recommendation=["2V64"], protein="Mad2" ),
    _pdb( id="2V64", label="Mad2 conformational dimer", recommendation=["1S2H"], protein="Mad2" ),
    _pdb( id="1TIM", label="Triosephosphate isomerase", recommendation=["4TIM"], protein="Triosephosphate isomerase" ),
    _pdb( id="4TIM", label="Triosephosphate isomerase", recommendation=["1TIM"], protein="Triosephosphate isomerase" ),
    _pdb( id="1UBQ", label="Ubiquitin", recommendation=["1UBI"], protein="Ubiquitin" ),
    _pdb( id="1UBI", label="Ubiquitin", recommendation=["1UBQ"], protein="Ubiquitin" ),
    _pdb( id="1H8H", label="F1-ATPase", recommendation=["1AKE", "4AKE"], protein="Bovine mitochondrial F1-ATPase" ),
    _pdb( id="1J85", label="YibK methyltransferase", recommendation=["1CSH"], protein="YibK / tRNA methyltransferase homolog" ),
    _pdb( id="1QLP", label="Alpha-1-antitrypsin", recommendation=["1CSH"], protein="Alpha-1-antitrypsin" ),
    _pdb( id="2RH1", label="Beta-2 adrenergic receptor", recommendation=["4OBE"], protein="Beta-2 adrenergic receptor" ),
    _pdb( id="4OBE", label="KRAS", recommendation=["2RH1"], protein="Human KRAS" ),
    _pdb( id="1CSH", label="Citrate synthase", recommendation=["1AKE", "4AKE"], protein="Citrate synthase" ),
)