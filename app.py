# app.py — entry point: page setup + router. Pages live in ui/pages/, routes in ui/route.py.
import streamlit as st

from ui.route import build_navigation
from ui.tailwind import inject_tailwind
from ui.theme import inject_css

st.set_page_config(page_title="FoldShield++", page_icon="🧬", layout="wide")
inject_css()
inject_tailwind()
build_navigation().run()
