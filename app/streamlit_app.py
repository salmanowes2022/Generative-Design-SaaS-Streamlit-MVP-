"""
Brand Asset Generator - Main Streamlit App
Entry point for the application
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from app.infra.config import settings
from app.infra.logging import get_logger
from app.core.router import router

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Brand Asset Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "org_id" not in st.session_state:
    # For MVP, use demo organization
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"

if "user_email" not in st.session_state:
    st.session_state.user_email = "demo@company.com"


def main():
    """Main landing page"""
    
    # Header
    st.title("🎨 Brand Asset Generator")
    st.subheader("Generate On-Brand Social Media Assets with AI")
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### AI-Powered Brand Design in 3 Simple Steps

        **Step 1**: Upload your brand book (PDF) - AI extracts everything automatically

        **Step 2**: Chat with AI - "Create a Black Friday Instagram post"

        **Step 3**: Download your design - Professional, on-brand, ready to post

        #### ✨ What You Get
        - 💬 **Chat to Create** - Just describe what you need
        - 📖 **Smart Brand Analysis** - Upload your brand book once, use forever
        - 🎨 **Professional Designs** - Large text, real people, brand colors
        - ⚡ **Fast** - No complex validation, just create
        - 📚 **All Your Designs** - Saved automatically
        """)
        
        # CTA buttons - Simple and clear
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if st.button("📖 1. Upload Brand Book", use_container_width=True, type="primary"):
                st.switch_page("pages/1_Onboard_Brand_Kit.py")

        with col_b:
            if st.button("💬 2. Create Designs", use_container_width=True, type="primary"):
                st.switch_page("pages/3_Chat_Create.py")

        with col_c:
            if st.button("📚 3. View Library", use_container_width=True):
                st.switch_page("pages/4_Library.py")
    
    with col2:
        # Organization summary
        try:
            summary = router.get_organization_summary(st.session_state.org_id)
            
            st.metric(
                label="Brand Kits",
                value=summary["brand_kits_count"]
            )
            
            st.metric(
                label="Assets Created",
                value=summary["recent_assets_count"]
            )
            
            st.metric(
                label="Credits Remaining",
                value=summary["usage"]["credits_remaining"],
                delta=f"-{summary['usage']['credits_used']} used"
            )
            
            # Quick stats
            if summary["job_stats"]:
                st.markdown("---")
                st.markdown("**Generation Stats**")
                st.write(f"✅ Completed: {summary['job_stats']['completed_jobs']}")
                st.write(f"❌ Failed: {summary['job_stats']['failed_jobs']}")
        
        except Exception as e:
            logger.error(f"Error loading summary: {str(e)}")
            st.error("Error loading dashboard data")
    
    # How it works section
    st.markdown("---")
    st.markdown("### 🚀 How It Works")

    step1, step2, step3 = st.columns(3)

    with step1:
        st.markdown("#### 1️⃣ Upload Brand Book")
        st.write("Upload your PDF brand guidelines once. AI extracts colors, fonts, voice, CTAs automatically.")

    with step2:
        st.markdown("#### 2️⃣ Chat to Create")
        st.write("Just describe what you need: 'Create a Black Friday Instagram post'. AI does the rest.")

    with step3:
        st.markdown("#### 3️⃣ Download")
        st.write("Professional design ready instantly. Large text, real people, your brand colors.")
    
    # Example gallery (placeholder)
    st.markdown("---")
    st.markdown("### 🎯 Example Outputs")
    st.info("💡 Tip: Your generated assets will appear in the Library after creation")
    
    # Footer
    st.markdown("---")
    footer_col1, footer_col2 = st.columns(2)

    with footer_col1:
        st.markdown(f"**Environment**: {settings.APP_ENV}")

    with footer_col2:
        st.markdown(f"**User**: {st.session_state.user_email}")


if __name__ == "__main__":
    main()