"""
accounts.py
Login and the "My sets" page for the Streamlit app.

In app/main.py:

    from accounts import current_user, my_sets_page, remember_set

    user = current_user()          # shows the login screen and stops if needed
    ...
    result = analyze_video(path)   # Praneet's pipeline
    remember_set(user, uploaded_video.name, result)
    ...
    my_sets_page(user)             # e.g. inside a "My sets" tab

Login:
  * If .streamlit/secrets.toml has an [auth] section, players log in with
    Google (Streamlit's built-in st.login).
  * If not, they type a name instead. Same saving and history, just no
    password. Good for testing and as a backup for the demo.
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from history import save_set, load_sets  # noqa: E402


# ---------------------------------------------------------------
# Login
# ---------------------------------------------------------------

def google_login_ready():
    """True when Google login is set up in .streamlit/secrets.toml."""
    try:
        return "auth" in st.secrets
    except Exception:          # no secrets file at all
        return False


def current_user():
    """Return the logged-in player's id (email or name). Stops the page if nobody is logged in."""
    if google_login_ready():
        if not st.user.is_logged_in:
            st.subheader("Log in to track your sets")
            st.button("Log in with Google", on_click=st.login)
            st.stop()
        with st.sidebar:
            st.write(f"Logged in as **{st.user.name}**")
            st.button("Log out", on_click=st.logout)
        return st.user.email

    # Backup: no Google login set up, so ask for a name
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


# ---------------------------------------------------------------
# Saving and history
# ---------------------------------------------------------------

def remember_set(user, video_name, result):
    """Save a set once, even though Streamlit reruns the page on every click."""
    key = f"saved::{video_name}::{result.get('score')}"
    if not st.session_state.get(key):
        save_set(user, video_name, result)
        st.session_state[key] = True


def my_sets_page(user):
    """Score-over-time chart and a table of past sets."""
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
