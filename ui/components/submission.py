"""Shared links for requesting additional protein structure uploads."""
import streamlit as st

SUBMISSION_URL = "https://rexcrux.com/foldshield/submission"


def submission_card(
    *,
    title: str = "Need another protein model?",
    description: str = "Request an upload so your structure can be compared in FoldShield.",
    key: str,
    button_label: str = "Request upload",
    layout: str = "wide",
) -> None:
    """Render a roomy, theme-native callout linking to the submission page."""
    with st.container(border=False, key=f"submission_card_{key}"):
        if layout == "vertical":
            st.caption("REQUEST A MODEL")
            st.subheader(title)
            st.write(description)
            st.link_button(
                button_label,
                SUBMISSION_URL,
                icon=":material/add:",
                key=f"{key}_link",
            )
            return

        # Keep the copy comfortably readable while reserving a clear action area.
        copy, action = st.columns([4.5, 1.5], vertical_alignment="center")
        copy.caption("REQUEST A MODEL")
        copy.subheader(title)
        copy.write(description)
        action.link_button(
            button_label,
            SUBMISSION_URL,
            icon=":material/add:",
            key=f"{key}_link",
        )
