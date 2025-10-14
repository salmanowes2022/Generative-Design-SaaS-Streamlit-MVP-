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
        ### Two-Stage Pipeline for Perfect Brand Consistency
        
        **Stage 1 - AI Creativity**: DALL-E 3 generates stunning backgrounds and scenes
        
        **Stage 2 - Brand Precision**: Deterministic overlay of your exact logos, fonts, and colors
        
        #### ✨ Key Features
        - 🎨 **AI-Powered Generation** - Create unique, high-quality images
        - 🎯 **Brand Enforcement** - Guaranteed color accuracy (Delta E < 2.0)
        - ✅ **Validation** - Automated quality checks for every asset
        - 💳 **Credit-Based Billing** - Pay only for what you use
        - 📚 **Asset Library** - Organized collection of all your creations
        """)
        
        # CTA buttons
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("🏁 Setup Brand Kit", use_container_width=True):
                st.switch_page("pages/1_Onboard_Brand_Kit.py")
        
        with col_b:
            if st.button("🎨 Generate Assets", use_container_width=True):
                st.switch_page("pages/2_Generate.py")
        
        with col_c:
            if st.button("📚 View Library", use_container_width=True):
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
    
    step1, step2, step3, step4 = st.columns(4)
    
    with step1:
        st.markdown("#### 1️⃣ Setup")
        st.write("Upload your logo, fonts, and define your color palette")
    
    with step2:
        st.markdown("#### 2️⃣ Generate")
        st.write("Describe your vision and let AI create beautiful backgrounds")
    
    with step3:
        st.markdown("#### 3️⃣ Compose")
        st.write("Apply your brand elements with pixel-perfect precision")
    
    with step4:
        st.markdown("#### 4️⃣ Validate")
        st.write("Get quality scores and download your on-brand assets")
    
    # Example gallery (placeholder)
    st.markdown("---")
    st.markdown("### 🎯 Example Outputs")
    st.info("💡 Tip: Your generated assets will appear in the Library after creation")
    
    # Footer
    st.markdown("---")
    footer_col1, footer_col2, footer_col3 = st.columns(3)
    
    with footer_col1:
        st.markdown(f"**Environment**: {settings.APP_ENV}")
    
    with footer_col2:
        st.markdown(f"**User**: {st.session_state.user_email}")
    
    with footer_col3:
        if st.button("💳 Manage Billing"):
            st.switch_page("pages/5_Billing.py")


if __name__ == "__main__":
    main()