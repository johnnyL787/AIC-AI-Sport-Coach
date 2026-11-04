
import streamlit as st

# ----------------------------------
# PAGE CONFIG
# ----------------------------------

st.set_page_config(
    page_title="Form Coach | Volleyball",
    page_icon="🏐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ----------------------------------
# STYLING
# ----------------------------------

st.markdown("""
<style>
    :root {
        --background: #f7f7f5;
        --surface: #ffffff;
        --text: #202522;
        --muted: #747a76;
        --border: #e5e6e1;
        --orange: #e75b35;
        --orange-hover: #d34b28;
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: var(--background);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .block-container {
        max-width: 760px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }

    /* Navigation */

    .nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 22px;
        border-bottom: 1px solid var(--border);
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 11px;
    }

    .brand-mark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        background: var(--orange);
        color: white;
        border-radius: 7px;
        font-weight: 800;
        font-size: 17px;
    }

    .brand-name {
        font-size: 16px;
        font-weight: 800;
        letter-spacing: -0.6px;
        color: var(--text);
    }

    .nav-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        color: var(--muted);
    }

    /* Hero */

    .hero {
        padding-top: 48px;
        padding-bottom: 38px;
    }

    .eyebrow {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.7px;
        color: var(--orange);
        margin-bottom: 13px;
    }

    .hero-title {
        color: var(--text);
        font-size: clamp(32px, 6vw, 43px);
        font-weight: 800;
        letter-spacing: -1.7px;
        line-height: 1.16;
        margin-bottom: 16px;
    }

    .hero-description {
        font-size: 15px;
        line-height: 1.7;
        color: var(--muted);
        max-width: 475px;
    }

    /* Step indicator */

    .steps {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 32px;
    }

    .step {
        display: flex;
        align-items: center;
        gap: 9px;
        white-space: nowrap;
        font-size: 12px;
        font-weight: 600;
        color: var(--muted);
    }

    .step-number {
        width: 26px;
        height: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #d8dad5;
        border-radius: 50%;
        font-size: 11px;
        font-weight: 700;
    }

    .step.active {
        color: var(--text);
    }

    .step.active .step-number {
        background: var(--orange);
        border-color: var(--orange);
        color: white;
    }

    .step-line {
        height: 1px;
        background: var(--border);
        flex: 1;
        min-width: 12px;
    }

    /* Section heading */

    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 17px;
    }

    .section-title {
        color: var(--text);
        font-size: 19px;
        font-weight: 750;
        letter-spacing: -0.5px;
    }

    .section-meta {
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* Uploader */

    [data-testid="stFileUploader"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px;
    }

    [data-testid="stFileUploader"] section {
        background: #fafaf9;
        border: 1px dashed #d2d5d0;
        border-radius: 8px;
        padding: 26px 12px;
    }

    [data-testid="stFileUploader"] section:hover {
        border-color: var(--orange);
        background: #fffaf7;
    }

    [data-testid="stFileUploader"] section button {
        background: #ffffff;
        color: var(--text);
        border: 1px solid #d8dad5;
        border-radius: 6px;
        font-weight: 600;
        box-shadow: none;
    }

    [data-testid="stFileUploader"] section button:hover {
        color: var(--orange);
        border-color: var(--orange);
    }

    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small {
        color: var(--text);
    }

    [data-testid="stFileUploader"] small {
        color: var(--muted);
    }

    /* Uploaded video */

    [data-testid="stVideo"] {
        border-radius: 8px;
        overflow: hidden;
    }

    .video-heading {
        margin-top: 23px;
        margin-bottom: 12px;
        font-size: 15px;
        font-weight: 700;
        color: var(--text);
    }

    .video-file {
        font-size: 12px;
        color: var(--muted);
        margin: 10px 0 23px;
        overflow-wrap: anywhere;
    }

    /* Primary action */

    div.stButton > button[kind="primary"] {
        background: var(--orange);
        border: 1px solid var(--orange);
        border-radius: 7px;
        color: white;
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

    div.stButton > button[kind="primary"]:focus {
        color: white;
    }

    div.stButton > button[kind="primary"] p {
        color: inherit;
    }

    /* Alerts */

    [data-testid="stAlert"] {
        border-radius: 7px;
        box-shadow: none;
    }

    /* Footer */

    .page-footer {
        border-top: 1px solid var(--border);
        margin-top: 55px;
        padding-top: 20px;
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-size: 11px;
        color: var(--muted);
    }

    @media (max-width: 600px) {
        .block-container {
            padding-top: 1.2rem;
        }

        .hero {
            padding-top: 34px;
            padding-bottom: 29px;
        }

        .steps {
            gap: 7px;
        }

        .step {
            font-size: 10px;
            gap: 5px;
        }

        .step-number {
            width: 22px;
            height: 22px;
        }

        .page-footer {
            flex-direction: column;
        }
    }

</style>
""", unsafe_allow_html=True)


# ----------------------------------
# NAVIGATION
# ----------------------------------

st.markdown("""
<div class="nav">
    <div class="brand">
        <div class="brand-mark">F</div>
        <div class="brand-name">FORM / COACH</div>
    </div>
    <div class="nav-label">VOLLEYBALL</div>
</div>
""", unsafe_allow_html=True)


# ----------------------------------
# HERO
# ----------------------------------

st.markdown("""
<div class="hero">
    <div class="eyebrow">MOVEMENT ANALYSIS</div>
    <div class="hero-title">
        Better form.<br>
        Better performance.
    </div>
    <div class="hero-description">
        Improve your volleyball setting technique through
        video analysis. Upload a recording of your form
        to get started.
    </div>
</div>
""", unsafe_allow_html=True)


# ----------------------------------
# UPLOAD SECTION
# ----------------------------------

st.markdown("""
<div class="steps">
    <div class="step active">
        <div class="step-number">1</div>
        Upload
    </div>
    <div class="step-line"></div>
    <div class="step">
        <div class="step-number">2</div>
        Analyze
    </div>
    <div class="step-line"></div>
    <div class="step">
        <div class="step-number">3</div>
        Results
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="section-header">
    <div class="section-title">Upload your video</div>
    <div class="section-meta">STEP 01</div>
</div>
""", unsafe_allow_html=True)

uploaded_video = st.file_uploader(
    "Choose a video of your volleyball setting technique",
    type=["mp4", "mov"],
    help="Accepted formats: MP4 and MOV.",
    label_visibility="collapsed",
)


# ----------------------------------
# VIDEO PREVIEW & ANALYZE
# ----------------------------------

if uploaded_video is not None:

    st.markdown(
        '<div class="video-heading">Video preview</div>',
        unsafe_allow_html=True
    )

    st.video(
        uploaded_video,
        format=uploaded_video.type or "video/mp4"
    )

    # File details
    file_size = uploaded_video.size / (1024 * 1024)

    st.markdown(
        f'<div class="video-file">'
        f'{uploaded_video.name} · {file_size:.1f} MB'
        f'</div>',
        unsafe_allow_html=True
    )

    # Placeholder for backend integration
    if st.button(
        "Analyze video",
        type="primary",
        use_container_width=True
    ):
        st.info(
            "Video analysis is coming soon. "
            "The form detection system is not connected yet."
        )

else:

    st.caption(
        "Supported formats: MP4, MOV. "
        "Record yourself setting a volleyball with your "
        "upper body clearly visible."
    )


# ----------------------------------
# FOOTER
# ----------------------------------

st.markdown("""
<div class="page-footer">
    <span>FORM / COACH</span>
    <span>Built by UCSD AI Collective</span>
</div>
""", unsafe_allow_html=True)
