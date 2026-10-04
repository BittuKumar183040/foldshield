"""Uploaded PDB handling: persist once per upload, detect chains. No layout code here."""
import os
import tempfile
from dataclasses import dataclass, field

import streamlit as st
from core.pdb.pdb_precheck import analyze_pdb


def fingerprint(upload):
    """Stable identity of an uploaded file across reruns (None if no upload)."""
    if upload is None:
        return None
    return getattr(upload, "file_id", None) or (upload.name, upload.size)


@dataclass
class PdbInput:
    path: str = ""
    chains: list = field(default_factory=list)
    fp: str = ""
    name: str = ""
    error: str = ""

    @property
    def ready(self) -> bool:
        return bool(self.path)


def save_upload(upload, suffix: str = ".pdb") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(upload.getvalue())
    return path


def detect_chains(path: str):
    """Return (chain_ids, error_message)."""
    try:
        return list(analyze_pdb(path)["chain_ids"]), ""
    except Exception as e:
        return [], f"analyze_pdb failed: {e}"


def resolve_pdb(slot: str, upload) -> PdbInput:
    """Write the upload to a temp file ONCE (not on every rerun) and cache chains."""
    key = f"pdb:{slot}"
    if upload is None:
        st.session_state.pop(key, None)
        return PdbInput()
    fp = str(fingerprint(upload))
    cached = st.session_state.get(key)
    if cached and cached.fp == fp:
        return cached
    path = save_upload(upload)
    chains, err = detect_chains(path)
    pdb = PdbInput(path=path, chains=chains, fp=fp, name=upload.name, error=err)
    st.session_state[key] = pdb
    return pdb
