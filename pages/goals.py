"""pages/goals.py — Insight Goals page (wraps insight_goals.py core module)."""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from insight_goals import render_goals_page

if st.session_state.get("df") is None:
    st.warning("⚠️ Please upload data first → **📂 Data Upload**.")
    st.stop()

render_goals_page()
