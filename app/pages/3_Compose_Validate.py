"""
Compose & Validate Page
Apply brand overlay and validate composition
"""
import streamlit as st
from uuid import UUID
from app.core.schemas import CompositionRequest, CompositionPreset, AssetType
from app.core.router import router
from app.core.brandkit import brand_kit_manager
from app.infra.db import db
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Compose & Validate", page_icon="🧱", layout="wide")

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"


def main():
    st.title("🧱 Compose & Validate")
    st.markdown("Apply your brand elements to the generated image")
    
    # Check if asset is selected
    if "selected_asset_id" not in st.session_state:
        st.warning("⚠️ Please generate an image first")
        if st.button("🎨 Go to Generate"):
            st.switch_page("pages/2_🎨_Generate.py")
        return
    
    # Load asset
    try:
        asset_data = db.fetch_one(
            "SELECT * FROM assets WHERE id = %s",
            (st.session_state.selected_asset_id,)
        )
        
        if not asset_data:
            st.error("❌ Asset not found")
            return
    
    except Exception as e:
        logger.error(f"Error loading asset: {str(e)}")
        st.error("Error loading asset")
        return
    
    # Display original image
    st.subheader("1️⃣ Original Generated Image")
    st.image(asset_data["base_url"], use_container_width=True)
    
    st.markdown("---")
    
    # Brand kit selection
    st.subheader("2️⃣ Select Brand Kit")
    
    try:
        brand_kits = brand_kit_manager.get_brand_kits_by_org(st.session_state.org_id)
        
        if not brand_kits:
            st.warning("⚠️ No brand kits found")
            return
        
        # Auto-select if coming from generate page
        default_kit = None
        if "selected_brand_kit_id" in st.session_state:
            default_kit = next(
                (kit for kit in brand_kits if str(kit.id) == st.session_state.selected_brand_kit_id),
                brand_kits[0]
            )
        else:
            default_kit = brand_kits[0]
        
        brand_kit_options = {kit.name: kit for kit in brand_kits}
        default_index = list(brand_kit_options.keys()).index(default_kit.name)
        
        selected_kit_name = st.selectbox(
            "Brand Kit",
            options=list(brand_kit_options.keys()),
            index=default_index
        )
        
        selected_kit = brand_kit_options[selected_kit_name]
        
        # Get brand assets
        logos = brand_kit_manager.get_brand_assets(selected_kit.id, AssetType.LOGO)
        fonts = brand_kit_manager.get_brand_assets(selected_kit.id, AssetType.FONT)
    
    except Exception as e:
        logger.error(f"Error loading brand kits: {str(e)}")
        st.error("Error loading brand kits")
        return
    
    # Composition form
    st.markdown("---")
    st.subheader("3️⃣ Composition Settings")
    
    with st.form("composition_form"):
        # Preset selection
        preset_options = {
            "Logo Top-Left, Text Bottom": CompositionPreset.TOP_LEFT_LOGO_BOTTOM_CTA,
            "Centered Logo Only": CompositionPreset.CENTER_LOGO_NO_TEXT,
            "Logo Bottom-Right, Text Top": CompositionPreset.BOTTOM_RIGHT_LOGO_TOP_TEXT
        }
        
        selected_preset_name = st.selectbox(
            "Composition Preset",
            options=list(preset_options.keys()),
            help="Choose how your brand elements will be arranged"
        )
        
        selected_preset = preset_options[selected_preset_name]
        
        # Preview of preset
        st.info(f"**{selected_preset_name}**: {'Logo will be overlaid according to the preset. Text is optional for this layout.' if 'Text' in selected_preset_name else 'Only logo will be centered, no text overlay.'}")
        
        # Text input (conditional)
        text = None
        if selected_preset != CompositionPreset.CENTER_LOGO_NO_TEXT:
            text = st.text_input(
                "Overlay Text (Optional)",
                placeholder="e.g., Shop Now, Learn More, Get Started",
                help="Call-to-action or headline text to overlay"
            )
        
        # Logo selection
        if logos:
            logo_options = {f"Logo {idx+1}": logo for idx, logo in enumerate(logos)}
            selected_logo_name = st.selectbox(
                "Select Logo",
                options=list(logo_options.keys())
            )
            selected_logo = logo_options[selected_logo_name]
            
            # Show logo preview
            with st.expander("Preview Logo"):
                st.image(selected_logo.url, width=200)
        else:
            st.warning("⚠️ No logos found in this brand kit")
            selected_logo = None
        
        # Font selection (optional)
        selected_font = None
        if fonts and text:
            font_options = {f"Font {idx+1}": font for idx, font in enumerate(fonts)}
            font_options["Default Font"] = None
            
            selected_font_name = st.selectbox(
                "Select Font",
                options=list(font_options.keys())
            )
            selected_font = font_options[selected_font_name]
        
        # Cost info
        from app.infra.billing import billing_manager
        st.info(f"💳 Composition will cost **{billing_manager.credits_per_composition} credits**")
        
        # Submit button
        submitted = st.form_submit_button("✨ Apply Brand Overlay", use_container_width=True)
        
        if submitted:
            if not selected_logo and selected_preset != CompositionPreset.CENTER_LOGO_NO_TEXT:
                st.error("❌ Please upload a logo to your brand kit first")
                return
            
            try:
                with st.spinner("🎨 Composing your branded asset..."):
                    # Create composition request
                    composition_request = CompositionRequest(
                        asset_id=UUID(st.session_state.selected_asset_id),
                        brand_kit_id=selected_kit.id,
                        preset=selected_preset,
                        text=text if text else None,
                        logo_asset_id=selected_logo.id if selected_logo else None,
                        font_asset_id=selected_font.id if selected_font else None
                    )
                    
                    # Compose and validate
                    result = router.compose_and_validate_workflow(
                        org_id=st.session_state.org_id,
                        composition_request=composition_request
                    )
                    
                    st.session_state.composed_url = result["composed_url"]
                    st.session_state.validation_result = result["validation"]
                    
                    st.success("✅ Composition complete!")
                    st.balloons()
            
            except Exception as e:
                logger.error(f"Error composing: {str(e)}")
                st.error(f"❌ Composition failed: {str(e)}")
                return
    
    # Display composed result
    if "composed_url" in st.session_state:
        st.markdown("---")
        st.subheader("4️⃣ Composed Image")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(st.session_state.composed_url, use_container_width=True)
        
        with col2:
            # Validation report
            st.markdown("### ✅ Validation Report")
            
            validation = st.session_state.validation_result
            
            # Logo verification
            if validation.logo_verified:
                st.success("✅ Logo Verified")
                if validation.logo_match_score:
                    st.progress(validation.logo_match_score / 100)
                    st.caption(f"Match Score: {validation.logo_match_score:.1f}%")
            else:
                st.info("ℹ️ Logo verification pending")
            
            # Color accuracy
            if validation.color_accuracy:
                st.success("✅ Color Accuracy")
                st.progress(validation.color_accuracy / 100)
                st.caption(f"Accuracy: {validation.color_accuracy:.1f}%")
                
                if validation.color_delta_e:
                    if validation.color_delta_e <= 2.0:
                        st.success(f"Delta E: {validation.color_delta_e:.2f} (Excellent)")
                    elif validation.color_delta_e <= 5.0:
                        st.warning(f"Delta E: {validation.color_delta_e:.2f} (Good)")
                    else:
                        st.error(f"Delta E: {validation.color_delta_e:.2f} (Needs Improvement)")
            
            # Font applied
            if validation.font_applied:
                st.success("✅ Brand Elements Applied")
            
            # Overall score
            st.markdown("---")
            overall_score = (
                (100 if validation.logo_verified else 0) +
                (validation.color_accuracy or 0) +
                (100 if validation.font_applied else 0)
            ) / 3
            
            st.metric("Overall Quality", f"{overall_score:.1f}%")
            
            # Download button
            st.markdown("---")
            st.download_button(
                label="📥 Download Image",
                data=st.session_state.composed_url,
                file_name="branded_asset.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
            
            # Next actions
            if st.button("📚 View in Library", use_container_width=True):
                st.switch_page("pages/4_📚_Library.py")
            
            if st.button("🎨 Generate More", use_container_width=True):
                st.switch_page("pages/2_🎨_Generate.py")
    
    # Tips
    st.markdown("---")
    with st.expander("💡 Composition Tips"):
        st.markdown("""
        **Preset Selection:**
        - **Top-Left Logo + Bottom Text**: Best for promotional posts, ads
        - **Centered Logo Only**: Best for profile pictures, brand awareness
        - **Bottom-Right Logo + Top Text**: Best for announcements, headers
        
        **Text Guidelines:**
        - Keep it short: 2-5 words work best
        - Use action verbs: "Shop Now", "Learn More", "Get Started"
        - Ensure text contrasts with background
        
        **Validation Scores:**
        - **Logo Verified**: Confirms your logo was applied correctly
        - **Color Accuracy (Delta E)**: Measures color precision
          - < 2.0 = Imperceptible difference (Excellent)
          - 2.0-5.0 = Perceptible but acceptable (Good)
          - > 5.0 = Noticeable difference (Review needed)
        - **Overall Quality**: Combined score of all checks
        """)


if __name__ == "__main__":
    main()