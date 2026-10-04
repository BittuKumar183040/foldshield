"""The only place that knows which session_state keys exist."""
import streamlit as st
from services.inputs import fingerprint
from services.pipeline import RunResult

_RESULT = "result"
_SUMMARY_FP = "summary_fp"


def get_result() -> RunResult | None:
    return st.session_state.get(_RESULT)


def set_result(result: RunResult) -> None:
    st.session_state[_RESULT] = result


def is_new_upload(upload) -> bool:
    """True once per newly chosen summary.json (so reruns don't reload it)."""
    fp = fingerprint(upload)
    if fp is None:
        st.session_state[_SUMMARY_FP] = None
        return False
    if st.session_state.get(_SUMMARY_FP) == fp:
        return False
    st.session_state[_SUMMARY_FP] = fp
    return True
