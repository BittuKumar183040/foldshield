import streamlit as st

from ui.footer import render_footer
from ui.route import build_navigation
from ui.theme import inject_css

st.set_page_config(page_title="FoldShield++", page_icon="🧬", layout="wide")
inject_css()
build_navigation().run()
render_footer()
