import os
import sys

import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from history import save_set, load_sets  # noqa: E402


def google_login_ready():
    try:
        return "auth" in st.secrets
    except Exception:        
        return False


def current_user():
    if google_login_ready():
        if not st.user.is_logged_in:
            st.subheader("Log in to track your sets")
            st.button("Log in with Google", on_click=st.login)
            st.stop()
        with st.sidebar:
            st.write(f"Logged in as **{st.user.name}**")
            st.button("Log out", on_click=st.logout)
        return st.user.email

    if not st.session_state.get("player"):
        st.subheader("Who's setting today?")
        name = st.text_input("Your name or email")
        if st.button("Start") and name.strip():
            st.session_state.player = name.strip()
            st.rerun()
        st.stop()
    with st.sidebar:
        st.write(f"Player: **{st.session_state.player}**")
        if st.button("Switch player"):
            del st.session_state.player
            st.rerun()
    return st.session_state.player


def remember_set(user, video_name, result):
    key = f"saved::{video_name}::{result.get('score')}"
    if not st.session_state.get(key):
        save_set(user, video_name, result)
        st.session_state[key] = True


def my_sets_page(user):
    sets = load_sets(user)
    if not sets:
        st.info("No sets yet. Upload a clip to start tracking.")
        return

    table = pd.DataFrame([{
        "Date": s["created_at"].replace("T", " ")[:16],
        "Video": s["video_name"],
        "Score": s["score"],
        "Out of": s["max_score"],
        "Main tip": s["main_tip"],
    } for s in sets])

    first, last = table["Score"].iloc[0], table["Score"].iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Sets logged", len(sets))
    col2.metric("Latest score", f"{last:.0f}" if last is not None else "-",
                delta=None if len(sets) < 2 or first is None or last is None
                else f"{last - first:+.0f} since first set")
    col3.metric("Best score", f"{table['Score'].max():.0f}")

    st.line_chart(table.set_index("Date")["Score"], y_label="Score")
    st.dataframe(table.iloc[::-1], hide_index=True, width="stretch")
