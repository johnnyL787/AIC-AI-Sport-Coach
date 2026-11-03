
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Sports Coach",
    page_icon="🏐",
    layout="centered"
)

# Custom styling
st.markdown("""
<style>
    .block-container {
        max-width: 800px;
        padding-top: 3rem;
    }

    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 750;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    [data-testid="stFileUploader"] {
        border: 2px dashed #64748b;
        border-radius: 14px;
        padding: 22px;
    }

    [data-testid="stFileUploader"] section {
        padding: 24px;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(
    '<div class="main-title">🏐 AI Sports Coach</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload your volleyball setting video and improve your technique.'
    '</div>',
    unsafe_allow_html=True
)

# Upload section
st.subheader("Upload Your Video")

uploaded_video = st.file_uploader(
    "Drag and drop your video here, or browse files",
    type=["mp4", "mov"],
    help="Upload a video of yourself setting a volleyball."
)

# Video preview
if uploaded_video is not None:
    st.success("Video uploaded successfully!")

    st.video(
        uploaded_video,
        format=uploaded_video.type
    )

    st.caption(f"File: {uploaded_video.name}")

    if st.button(
        "✨ Analyze Video",
        type="primary",
        use_container_width=True
    ):
        st.info("AI form analysis is coming soon!")

else:
    st.info("Upload an MP4 or MOV video to get started.")

st.divider()

st.caption(
    "AI Sports Coach | Built by UCSD AI Collective"
)
