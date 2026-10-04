import json
import streamlit as st
from ui.components import empty_state, section


def render_log(result) -> None:
    if not result:
        empty_state("No run yet", "Pipeline output and the raw summary appear here.")
        return
    if result.error:
        st.error(result.error)
    if result.log.strip():
        section("Run log")
        st.code(result.log)
    if result.summary:
        section("Raw summary.json")
        st.download_button("Download summary.json", json.dumps(result.summary, indent=2),
                           file_name="summary.json", mime="application/json")
        st.json(result.summary, expanded=False)
