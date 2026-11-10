
import streamlit as st
from html import escape

# -------------------------------------------------
# PAGE SETUP
# -------------------------------------------------

st.set_page_config(
    page_title="Form Coach | Volleyball",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------
# STYLING
# -------------------------------------------------

st.markdown("""
<style>
    :root {
        --orange: #ff630d;
        --orange-hover: #e75509;
        --black: #171717;
        --muted: #78716c;
        --bg: #faf9f6;
        --border: #e7e5e2;
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: var(--bg);
        color: var(--black);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1080px;
        padding: 2rem 2.5rem 4rem;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    /* Header */

    .app-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid var(--border);
        padding-bottom: 20px;
    }

    .app-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 16px;
        font-weight: 800;
        color: var(--black);
        letter-spacing: -0.4px;
    }

    .brand-mark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 6px;
        background: var(--orange);
        color: white;
        font-size: 21px;
    }

    .app-chapter {
        font-size: 11px;
        letter-spacing: 1px;
        font-weight: 650;
        color: var(--muted);
    }

    /* Hero */

    .hero {
        padding: 48px 0 35px;
    }

    .eyebrow {
        font-size: 11px;
        font-weight: 750;
        letter-spacing: 1.3px;
        color: var(--orange);
        margin-bottom: 13px;
    }

    .hero-title {
        font-size: clamp(31px, 5vw, 43px);
        font-weight: 800;
        letter-spacing: -1.6px;
        color: var(--black);
        line-height: 1.2;
        margin-bottom: 12px;
    }

    .hero-description {
        font-size: 15px;
        line-height: 1.7;
        color: var(--muted);
        max-width: 650px;
    }

    /* Workspace */

    .st-key-workspace {
        background: white;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 30px;
    }

    .section-number {
        font-size: 11px;
        font-weight: 750;
        color: var(--orange);
        letter-spacing: 1px;
        margin-bottom: 7px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 750;
        letter-spacing: -0.5px;
        color: var(--black);
        margin-bottom: 6px;
    }

    .section-description {
        font-size: 13px;
        line-height: 1.6;
        color: var(--muted);
        margin-bottom: 22px;
    }

    /* Input labels */

    .st-key-workspace
    [data-testid="stWidgetLabel"] p {
        color: #38342f;
        font-size: 13px;
        font-weight: 650;
    }

    /* Select and text input */

    .st-key-workspace
    [data-baseweb="select"] > div {
        background: #ffffff;
        border: 1px solid #d9d6d1;
        border-radius: 6px;
        color: var(--black);
        min-height: 44px;
    }

    .st-key-workspace
    [data-baseweb="select"] span,
    .st-key-workspace
    [data-baseweb="select"] input {
        color: var(--black);
    }

    .st-key-workspace
    [data-testid="stTextInput"] input {
        background: white;
        color: var(--black);
        border: 1px solid #d9d6d1;
        border-radius: 6px;
    }

    /* File uploader */

    [data-testid="stFileUploader"] {
        background: #faf9f6;
        border: 1px dashed #d6d1ca;
        border-radius: 8px;
        padding: 12px;
    }

    [data-testid="stFileUploader"] section {
        background: transparent;
        border: none;
        padding: 22px 8px;
    }

    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small {
        color: #44403c;
    }

    [data-testid="stFileUploader"] button {
        background: white;
        color: var(--black);
        border: 1px solid #d6d1ca;
        border-radius: 6px;
    }

    [data-testid="stFileUploader"] button:hover {
        border-color: var(--orange);
        color: var(--orange);
    }

    /* Primary button */

    div.stButton > button[kind="primary"] {
        background: var(--orange);
        border: 1px solid var(--orange);
        color: white;
        border-radius: 6px;
        min-height: 48px;
        font-size: 14px;
        font-weight: 700;
        box-shadow: none;
    }

    div.stButton > button[kind="primary"]:hover {
        background: var(--orange-hover);
        border-color: var(--orange-hover);
        color: white;
    }

    div.stButton > button[kind="primary"] p {
        color: inherit;
    }

    /* Video */

    [data-testid="stVideo"] {
        border-radius: 7px;
        overflow: hidden;
    }

    .file-info {
        font-size: 12px;
        color: var(--muted);
        padding: 10px 0;
        overflow-wrap: anywhere;
    }

    /* Feedback */

    .feedback-box {
        background: #faf9f6;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 22px;
        min-height: 180px;
    }

    .feedback-title {
        font-size: 14px;
        font-weight: 700;
        color: var(--black);
        margin-bottom: 10px;
    }

    .feedback-description {
        font-size: 13px;
        line-height: 1.7;
        color: var(--muted);
    }

    /* Other text */

    .st-key-workspace .stCaption p {
        color: var(--muted);
    }

    .st-key-workspace hr {
        border-color: var(--border);
        margin: 28px 0;
    }

    .app-footer {
        border-top: 1px solid var(--border);
        padding-top: 20px;
        margin-top: 45px;
        display: flex;
        justify-content: space-between;
        color: var(--muted);
        font-size: 12px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding: 1rem 1rem 2rem;
        }

        .st-key-workspace {
            padding: 20px;
        }

        .hero {
            padding: 35px 0 25px;
        }

        .app-chapter {
            font-size: 9px;
        }

        .app-footer {
            flex-direction: column;
            gap: 8px;
        }
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# NAVIGATION
# -------------------------------------------------

st.markdown("""
<div class="app-nav">
    <div class="app-brand">
        <div class="brand-mark">F</div>
        FORM COACH
    </div>
    <div class="app-chapter">
        AI COLLECTIVE / UCSD
    </div>
</div>
""", unsafe_allow_html=True)


# -------------------------------------------------
# HERO
# -------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="eyebrow">
        VOLLEYBALL MOVEMENT ANALYSIS
    </div>
    <div class="hero-title">
        Improve your technique.
    </div>
    <div class="hero-description">
        Upload a video of your volleyball setting
        technique and provide a few details about
        your movement to prepare for form analysis.
    </div>
</div>
""", unsafe_allow_html=True)


# -------------------------------------------------
# WORKSPACE
# -------------------------------------------------

with st.container(key="workspace"):

    # PLAYER DETAILS

    st.markdown("""
    <div class="section-number">
        01 / PLAYER DETAILS
    </div>
    <div class="section-title">
        Movement information
    </div>
    <div class="section-description">
        Tell us about your stance and the type
        of volleyball set you're performing.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        dominant_hand = st.selectbox(
            "Dominant hand",
            [
                "Right-handed",
                "Left-handed",
                "Ambidextrous"
            ],
            index=None,
            placeholder="Choose an option"
        )

    with col2:
        lead_leg = st.selectbox(
            "Preferred lead leg",
            [
                "Right",
                "Left",
                "No preference",
                "Not sure"
            ],
            index=None,
            placeholder="Choose an option",
            help=(
                "Which foot do you typically position "
                "slightly forward when setting?"
            )
        )

    st.write("")

    col3, col4 = st.columns(2, gap="medium")

    with col3:
        set_type = st.selectbox(
            "Type of set",
            [
                "High / Outside",
                "Quick / Middle",
                "Back set",
                "Shoot / Fast",
                "Pipe / Back-row",
                "Other"
            ],
            index=None,
            placeholder="Choose a set type"
        )

        custom_set = ""

        if set_type == "Other":
            custom_set = st.text_input(
                "Specify set type",
                placeholder="Enter your set type",
                max_chars=80
            )

    with col4:
        set_direction = st.selectbox(
            "Setting direction",
            [
                "Left",
                "Right",
                "Straight ahead",
                "Not sure"
            ],
            index=None,
            placeholder="Choose a direction",
            help=(
                "Direction relative to the player, "
                "not the camera."
            )
        )

    st.divider()

    # VIDEO ANALYSIS

    st.markdown("""
    <div class="section-number">
        02 / VIDEO ANALYSIS
    </div>
    <div class="section-title">
        Upload your recording
    </div>
    <div class="section-description">
        Upload an MP4 or MOV video. A preview will
        appear once the file has been selected.
    </div>
    """, unsafe_allow_html=True)

    video_col, feedback_col = st.columns(
        [1.2, 1],
        gap="large"
    )

    with video_col:

        st.markdown("**Video**")

        uploaded_video = st.file_uploader(
            "Upload video",
            type=["mp4", "mov"],
            label_visibility="collapsed"
        )

        if uploaded_video is not None:

            st.video(uploaded_video)

            filename = escape(uploaded_video.name)
            size_mb = (
                uploaded_video.size / (1024 * 1024)
            )

            st.markdown(
                f'<div class="file-info">'
                f'{filename} · {size_mb:.1f} MB'
                f'</div>',
                unsafe_allow_html=True
            )

        else:

            st.caption(
                "Keep your upper body and feet "
                "visible in the recording."
            )

    with feedback_col:

        st.markdown("**Technique feedback**")

        st.markdown("""
        <div class="feedback-box">
            <div class="feedback-title">
                Analysis not available yet
            </div>
            <div class="feedback-description">
                Once the movement analysis backend
                is connected, this section will
                display feedback on your setting
                technique.
                <br><br>
                No analysis has been performed.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # ANALYZE BUTTON

    if st.button(
        "Analyze video",
        type="primary",
        use_container_width=True,
        disabled=uploaded_video is None
    ):

        if not dominant_hand:
            st.warning(
                "Please select your dominant hand."
            )

        elif not lead_leg:
            st.warning(
                "Please select your preferred lead leg."
            )

        elif not set_type:
            st.warning(
                "Please select your set type."
            )

        elif set_type == "Other" and not custom_set.strip():
            st.warning(
                "Please enter your set type."
            )

        elif not set_direction:
            st.warning(
                "Please select your setting direction."
            )

        else:

            analysis_request = {
                "dominant_hand": dominant_hand,
                "lead_leg": lead_leg,
                "set_type": (
                    custom_set.strip()
                    if set_type == "Other"
                    else set_type
                ),
                "set_direction": set_direction,
                "video_name": uploaded_video.name
            }

            st.session_state["analysis_request"] = (
                analysis_request
            )

            st.info(
                "Your video and movement details "
                "are ready. Automated analysis "
                "will be available soon."
            )


# -------------------------------------------------
# FOOTER
# -------------------------------------------------

st.markdown("""
<div class="app-footer">
    <span>FORM COACH</span>
    <span>Built by UCSD AI Collective</span>
</div>
""", unsafe_allow_html=True)
