"""Running the pipeline / loading a saved summary. Returns plain data, never touches layout."""
import contextlib
import io
import json
import os
import tempfile
import traceback
from dataclasses import dataclass


@dataclass
class RunResult:
    summary: dict | None = None
    outdir: str = ""
    log: str = ""
    error: str = ""

    @property
    def artifacts_dir(self) -> str:
        if self.outdir:
            return self.outdir
        return ((self.summary or {}).get("inputs") or {}).get("outdir") or ""


def run_pipeline(ref_path, query_path, *, mode, keep_hetatm, ref_chain, query_chain) -> RunResult:
    outdir = os.path.join(tempfile.mkdtemp(prefix="foldshield_"), "results")
    os.makedirs(outdir, exist_ok=True)
    cfg = {
        "pdb_ref": ref_path,
        "pdb_query": query_path,
        "outdir": outdir,
        "keep_hetatm": bool(keep_hetatm),
        "mode": mode,
        "ref_chain_id": ref_chain,
        "query_chain_id": query_chain,
    }
    buf = io.StringIO()
    try:
        from main import main as foldshield_main
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            foldshield_main(cfg)
    except Exception as e:
        return RunResult(outdir=outdir, log=buf.getvalue() + "\n" + traceback.format_exc(), error=str(e))

    summary = None
    path = os.path.join(outdir, "summary.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            summary = json.load(f)
    return RunResult(summary=summary, outdir=outdir, log=buf.getvalue())


def load_summary_upload(upload) -> RunResult:
    try:
        data = json.loads(upload.getvalue().decode("utf-8"))
    except Exception as e:
        return RunResult(error=f"Failed to parse summary.json: {e}")
    return RunResult(summary=data, outdir=(data.get("inputs") or {}).get("outdir") or "")
