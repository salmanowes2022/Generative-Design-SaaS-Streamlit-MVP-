"""
Onboard Brand Kit Page
Upload logos, fonts, and define brand guidelines
"""
import streamlit as st
from io import BytesIO
from app.core.schemas import BrandKitCreate, BrandColors, BrandStyle
from app.core.router import router
from app.core.brandkit import brand_kit_manager
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Onboard Brand Kit", page_icon="🏁", layout="wide")

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"


def main():
    st.title("🏁 Onboard Brand Kit")
    st.markdown("Define your brand guidelines for consistent asset generation")
    
    # Check existing brand kits
    try:
        from uuid import UUID
        org_id = UUID(st.session_state.org_id)
        existing_kits = brand_kit_manager.get_brand_kits_by_org(org_id)
        
        if existing_kits:
            st.success(f"✅ You have {len(existing_kits)} brand kit(s)")
            
            # Show existing kits
            with st.expander("View Existing Brand Kits"):
                for kit in existing_kits:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{kit.name}**")
                        st.write(f"Created: {kit.created_at.strftime('%Y-%m-%d')}")
                        st.write(f"Colors: {kit.colors.primary}, {kit.colors.secondary or 'N/A'}")
                    with col2:
                        if st.button(f"Edit", key=f"edit_{kit.id}"):
                            st.info("Edit functionality coming soon!")
            
            st.markdown("---")
    
    except Exception as e:
        logger.error(f"Error loading brand kits: {str(e)}")
        st.error("Error loading existing brand kits")
    
    # Create new brand kit form
    st.markdown("## Create New Brand Kit")
    
    with st.form("brand_kit_form"):
        # Basic info
        st.subheader("1️⃣ Basic Information")
        brand_name = st.text_input(
            "Brand Kit Name",
            placeholder="e.g., Summer Campaign 2024",
            help="A descriptive name for this brand kit"
        )
        
        # Colors
        st.subheader("2️⃣ Color Palette")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            primary_color = st.color_picker("Primary Color", "#2563EB")
        
        with col2:
            secondary_color = st.color_picker("Secondary Color", "#7C3AED")
        
        with col3:
            accent_color = st.color_picker("Accent Color", "#F59E0B")
        
        col4, col5 = st.columns(2)
        
        with col4:
            background_color = st.color_picker("Background Color", "#FFFFFF")
        
        with col5:
            text_color = st.color_picker("Text Color", "#1F2937")
        
        # Style descriptors
        st.subheader("3️⃣ Style & Voice")
        
        style_options = [
            "modern", "professional", "clean", "minimalist", "bold",
            "playful", "elegant", "corporate", "creative", "luxurious"
        ]
        
        selected_styles = st.multiselect(
            "Style Descriptors",
            options=style_options,
            default=["modern", "professional", "clean"],
            help="Select words that describe your brand's visual style"
        )
        
        voice = st.text_input(
            "Brand Voice",
            placeholder="e.g., confident and approachable",
            help="Describe your brand's communication tone"
        )
        
        mood = st.text_input(
            "Brand Mood",
            placeholder="e.g., innovative and trustworthy",
            help="Describe the emotional feeling of your brand"
        )
        
        # File uploads
        st.subheader("4️⃣ Brand Assets")
        
        st.info("ℹ️ **MVP Note**: File uploads are temporarily disabled. You can still create brand kits with colors and styles. Logo/font upload will be enabled after fixing Supabase storage configuration.")
        
        col_logo, col_font = st.columns(2)
        
        with col_logo:
            st.markdown("**Logo Upload**")
            logo_file = st.file_uploader(
                "Upload Logo (PNG/SVG)",
                type=["png", "svg"],
                help="Your brand logo - will be overlaid on generated images"
            )
            
            if logo_file:
                st.success(f"✅ {logo_file.name}")
        
        with col_font:
            st.markdown("**Font Upload** (Optional)")
            font_file = st.file_uploader(
                "Upload Font (TTF/OTF/WOFF)",
                type=["ttf", "otf", "woff", "woff2"],
                help="Custom font for text overlays (TTF, OTF, WOFF, or WOFF2 formats)"
            )
            
            if font_file:
                st.success(f"✅ {font_file.name}")
        
        # Submit button
        st.markdown("---")
        submitted = st.form_submit_button("🚀 Create Brand Kit", use_container_width=True)
        
        if submitted:
            # Validation
            if not brand_name:
                st.error("❌ Please enter a brand kit name")
                return
            
            if not selected_styles:
                st.error("❌ Please select at least one style descriptor")
                return
            
            try:
                with st.spinner("Creating brand kit..."):
                    # Create brand kit data
                    brand_kit_data = BrandKitCreate(
                        name=brand_name,
                        colors=BrandColors(
                            primary=primary_color,
                            secondary=secondary_color,
                            accent=accent_color,
                            background=background_color,
                            text=text_color
                        ),
                        style=BrandStyle(
                            descriptors=selected_styles,
                            voice=voice if voice else None,
                            mood=mood if mood else None
                        )
                    )
                    
                    # Prepare file uploads
                    logo_data = None
                    if logo_file:
                        logo_data = BytesIO(logo_file.read())
                    
                    font_data = None
                    if font_file:
                        font_data = BytesIO(font_file.read())
                    
                    # Create brand kit with assets
                    result = router.create_brand_kit_with_assets(
                        org_id=org_id,
                        brand_kit_data=brand_kit_data,
                        logo_file=logo_data,
                        font_file=font_data
                    )
                    
                    st.success("✅ Brand kit created successfully!")
                    
                    # Show summary
                    st.balloons()
                    
                    st.markdown("### ✨ Brand Kit Summary")
                    st.write(f"**Name**: {result['brand_kit'].name}")
                    st.write(f"**Colors**: {result['brand_kit'].colors.primary}, {result['brand_kit'].colors.secondary}")
                    st.write(f"**Style**: {', '.join(result['brand_kit'].style.descriptors)}")
                    st.write(f"**Assets**: {len(result['assets'])} uploaded")
                    
                    # Next steps
                    st.markdown("---")
                    col_next1, col_next2 = st.columns(2)
                    
                    with col_next1:
                        if st.button("🎨 Start Generating Assets", use_container_width=True):
                            st.session_state.selected_brand_kit_id = str(result['brand_kit'].id)
                            st.switch_page("pages/2_Generate.py")
                    
                    with col_next2:
                        if st.button("🏠 Back to Home", use_container_width=True):
                            st.switch_page("streamlit_app.py")
            
            except Exception as e:
                logger.error(f"Error creating brand kit: {str(e)}")
                st.error(f"❌ Error: {str(e)}")
    
    # Tips section
    st.markdown("---")
    with st.expander("💡 Tips for Great Brand Kits"):
        st.markdown("""
        **Colors:**
        - Choose colors that represent your brand identity
        - Ensure good contrast between text and background colors
        - Primary color will be used most prominently
        
        **Style Descriptors:**
        - Select 3-5 words that best describe your visual style
        - These guide the AI in generating appropriate imagery
        - Be specific: "minimalist" vs "bold and dramatic"
        
        **Logo:**
        - PNG with transparent background works best
        - Ensure logo is high resolution (at least 512x512px)
        - Will be automatically resized to fit compositions
        
        **Fonts:**
        - TTF and OTF formats supported
        - Custom fonts optional - default font available
        - Make sure you have rights to use the font commercially
        """)


if __name__ == "__main__":
    main()