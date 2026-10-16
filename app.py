import streamlit as st

from ui.route import build_navigation
from ui.theme import inject_css

st.set_page_config(page_title="FoldShield++", layout="wide")
inject_css()
build_navigation().run()
