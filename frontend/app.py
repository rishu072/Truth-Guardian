"""
Truth Guardian — Streamlit Interface

Lightweight standalone app for text, image, and social media detection.
Calls the Django REST API endpoints.
"""

import streamlit as st
import requests
import json
import os

# ── Configuration ──────────────────────────────────────────────────────────────

API_BASE = os.getenv("DJANGO_API_BASE", "http://localhost:8000")

# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Truth Guardian AI — Fake News Detector",
    page_icon="🛡️",
    layout="centered",
)

# ── Custom Styling ─────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    }
    .verdict-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 8px 0;
    }
    .badge-green  { background-color: #22c55e; color: #fff; }
    .badge-yellow { background-color: #eab308; color: #000; }
    .badge-red    { background-color: #ef4444; color: #fff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────────────

st.title("🛡️ Truth Guardian AI")
st.markdown(
    "Detect fake news with advanced AI. Verify text, images, and social media posts."
)
st.divider()

# ── Helpers ────────────────────────────────────────────────────────────────────


def render_result(data: dict):
    """Display the analysis result with colour-coded badge and evidence links."""
    if "error" in data and data.get("verdict") == "Error":
        st.error(f"❌ Error: {data.get('reason', data.get('error', 'Unknown error'))}")
        return

    score = int(data.get("truth_score", 0))
    verdict = data.get("verdict", "Unknown")

    # Colour badge
    if score >= 70:
        badge_class = "badge-green"
        icon = "✅"
    elif score >= 40:
        badge_class = "badge-yellow"
        icon = "⚠️"
    else:
        badge_class = "badge-red"
        icon = "🚨"

    st.markdown(
        f'<div class="verdict-badge {badge_class}">{icon} {verdict}</div>',
        unsafe_allow_html=True,
    )

    st.subheader(f"📊 Truth Score: {score}/100")
    st.progress(score)

    st.markdown(f"**📝 Analysis:** {data.get('reason', 'No explanation provided.')}")

    links = data.get("evidence_links", [])
    if links:
        st.markdown("**🔗 Evidence Links:**")
        for link in links:
            st.markdown(f"- [{link}]({link})")


# ── Tabs ───────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📝 Text Check", "🖼️ Image Check", "🌐 Social Media Check"])

# ── Tab 1: Text ────────────────────────────────────────────────────────────────

with tab1:
    st.subheader("🔍 Verify a News Claim (Text)")
    text = st.text_area(
        "Enter the news claim or article text:",
        height=180,
        placeholder="Paste a news headline or article text here…",
    )

    if st.button("Verify Text", key="btn_text"):
        if not text or not text.strip():
            st.warning("⚠️ Please enter a news claim.")
        else:
            with st.spinner("🔄 Analysing with AI…"):
                try:
                    res = requests.post(
                        f"{API_BASE}/api/detect/text/",
                        headers={"Content-Type": "application/json"},
                        json={"content": text},
                        timeout=120,
                    )
                    data = res.json()
                    render_result(data)
                except requests.exceptions.ConnectionError:
                    st.error(
                        "❌ Could not connect to the backend. "
                        "Make sure the Django server is running."
                    )
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ── Tab 2: Image ───────────────────────────────────────────────────────────────

with tab2:
    st.subheader("🖼️ Upload Image + Claim")
    uploaded_file = st.file_uploader(
        "Upload an image (JPG / PNG / WebP)",
        type=["jpg", "jpeg", "png", "webp"],
    )
    claim_text = st.text_input(
        "Optional claim / description of the image",
        placeholder="e.g. 'This photo shows a real flood in 2026'",
    )

    if st.button("Verify Image", key="btn_image"):
        if not uploaded_file:
            st.warning("⚠️ Please upload an image.")
        else:
            with st.spinner("🔄 Analysing image with AI…"):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file,
                            uploaded_file.type,
                        )
                    }
                    form_data = {}
                    if claim_text:
                        form_data["query"] = claim_text

                    res = requests.post(
                        f"{API_BASE}/api/detect/image/",
                        files=files,
                        data=form_data,
                        timeout=120,
                    )
                    data = res.json()
                    render_result(data)
                except requests.exceptions.ConnectionError:
                    st.error(
                        "❌ Could not connect to the backend. "
                        "Make sure the Django server is running."
                    )
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ── Tab 3: Social Media ───────────────────────────────────────────────────────

with tab3:
    st.subheader("🌐 Verify a Social Media Post")
    social_url = st.text_input(
        "Social Media Post URL",
        placeholder="https://twitter.com/user/status/123456",
    )
    social_claim = st.text_input(
        "Claim to verify (optional)",
        placeholder="e.g. 'This post claims that…'",
    )

    if st.button("Verify Social Post", key="btn_social"):
        if not social_url or not social_url.strip():
            st.warning("⚠️ Please enter a social media URL.")
        else:
            with st.spinner("🔄 Analysing social media post with AI…"):
                try:
                    payload = {
                        "url": social_url.strip(),
                        "claim": social_claim or "Verify the claim and check if it is true.",
                    }
                    res = requests.post(
                        f"{API_BASE}/api/detect/social/",
                        headers={"Content-Type": "application/json"},
                        json=payload,
                        timeout=120,
                    )
                    data = res.json()
                    render_result(data)
                except requests.exceptions.ConnectionError:
                    st.error(
                        "❌ Could not connect to the backend. "
                        "Make sure the Django server is running."
                    )
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────

st.divider()
st.caption("🛡️ Truth Guardian AI — Powered by Google Gemini & Django")
