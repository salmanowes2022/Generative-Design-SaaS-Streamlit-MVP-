"""
Canva Template Management
Browse and configure Canva templates for brand kits
"""
import streamlit as st
from uuid import UUID
from app.core.canva_oauth_bridge import canva_oauth_bridge, render_canva_auth_button
from app.core.renderer_canva import CanvaRenderer
from app.core.brandkit import brand_kit_manager
from app.core.brand_brain import brand_brain, BrandTokens
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Canva Templates", page_icon="🎨", layout="wide")

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"

if "user_id" not in st.session_state:
    st.session_state.user_id = "00000000-0000-0000-0000-000000000011"  # Demo user UUID


def main():
    st.title("🎨 Canva Template Library")
    st.markdown("Manage your Canva brand templates for automated design generation")

    # Canva authentication section
    st.sidebar.header("🔗 Canva Connection")
    render_canva_auth_button()

    # Check if authenticated
    if not canva_oauth_bridge.is_authenticated():
        st.info("👆 Connect to Canva to access templates")
        st.markdown("---")
        st.markdown("""
        ### What are Brand Templates?

        Brand templates are pre-designed Canva templates that follow your brand guidelines.
        They allow for automatic design generation with dynamic content like:

        - **Headlines** - Dynamic text for main messages
        - **Subheads** - Supporting text
        - **CTA Buttons** - Call-to-action text
        - **Images** - AI-generated backgrounds
        - **Colors** - Brand color palettes

        Connect your Canva account to start using templates!
        """)
        return

    # Get access token
    access_token = canva_oauth_bridge.get_access_token()
    if not access_token:
        st.error("Failed to get access token. Please reconnect to Canva.")
        return

    # Initialize renderer
    renderer = CanvaRenderer(access_token=access_token)

    # Brand kit selection
    st.sidebar.header("⚙️ Settings")

    try:
        # Convert org_id to UUID if it's a string
        org_id = st.session_state.org_id
        if isinstance(org_id, str):
            org_id = UUID(org_id)

        brand_kits = brand_kit_manager.get_brand_kits_by_org(org_id)

        if not brand_kits:
            st.warning("⚠️ No brand kits found. Please create one first.")
            if st.button("🏁 Create Brand Kit"):
                st.switch_page("pages/1_Onboard_Brand_Kit.py")
            return

        # Brand kit selector
        brand_kit_options = {kit.name: kit for kit in brand_kits}
        selected_kit_name = st.sidebar.selectbox(
            "Brand Kit",
            options=list(brand_kit_options.keys()),
            help="Select brand kit to configure templates for"
        )

        selected_kit = brand_kit_options[selected_kit_name]

        # Load Brand Brain (returns tuple of (tokens, policies))
        tokens, policies = brand_brain.get_brand_brain(selected_kit.id)

        if not tokens:
            st.sidebar.warning("⚠️ Brand Brain not configured")
            tokens = BrandTokens.get_default_tokens()
            policies = None

    except Exception as e:
        logger.error(f"Error loading brand kits: {str(e)}")
        st.error("Error loading brand kits")
        return

    st.sidebar.markdown("---")

    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📚 Browse Templates", "⚙️ Configure", "👤 Profile"])

    # TAB 1: Browse Templates
    with tab1:
        st.markdown("### Available Brand Templates")

        if st.button("🔄 Refresh Templates"):
            st.session_state.templates_cache = None
            st.rerun()

        # Fetch templates
        with st.spinner("Loading templates from Canva..."):
            templates = renderer.list_brand_templates(limit=50)

        if not templates:
            st.info("No brand templates found. Create templates in Canva with placeholders.")
            st.markdown("""
            #### How to create a brand template:

            1. Go to Canva and create a design
            2. Add text placeholders named:
               - `HEADLINE` - Main headline text
               - `SUBHEAD` - Supporting text
               - `CTA_TEXT` - Call-to-action button
            3. Add image placeholders named:
               - `BG_IMAGE` - Background image
               - `PRODUCT_IMAGE` - Product image (optional)
            4. Save as a Brand Template
            5. Refresh this page to see it here
            """)
            return

        st.success(f"Found {len(templates)} templates")

        # Display templates in grid
        cols = st.columns(3)

        for idx, template in enumerate(templates):
            with cols[idx % 3]:
                with st.container(border=True):
                    # Template thumbnail
                    thumbnail = template.get("thumbnail", {}).get("url")
                    if thumbnail:
                        st.image(thumbnail, use_container_width=True)
                    else:
                        st.markdown("**No thumbnail**")

                    # Template info
                    st.markdown(f"**{template.get('name', 'Untitled')}**")
                    st.caption(f"ID: `{template.get('id')}`")

                    # Dimensions
                    width = template.get("width", {}).get("value", 0)
                    height = template.get("height", {}).get("value", 0)
                    if width and height:
                        st.caption(f"Size: {width}x{height}px")

                    # Add to brand kit button
                    if st.button(
                        "➕ Add to Brand Kit",
                        key=f"add_template_{template.get('id')}",
                        use_container_width=True
                    ):
                        st.session_state.template_to_add = template
                        st.rerun()

    # TAB 2: Configure Templates for Channels
    with tab2:
        st.markdown("### Template Configuration")
        st.caption("Map templates to channels and aspect ratios")

        # Current template mappings
        st.markdown("#### Current Mappings")

        if tokens.templates:
            for key, template_id in tokens.templates.items():
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.text(key)
                with col2:
                    st.code(template_id)
                with col3:
                    if st.button("🗑️", key=f"remove_{key}"):
                        # Remove template mapping
                        updated_templates = tokens.templates.copy()
                        del updated_templates[key]
                        tokens.templates = updated_templates

                        # Save to Brand Brain
                        brand_brain.save_brand_brain(
                            selected_kit.id,
                            tokens=tokens,
                            policies=policies
                        )

                        st.success("Template mapping removed")
                        st.rerun()
        else:
            st.info("No template mappings configured yet")

        st.markdown("---")

        # Add new mapping
        st.markdown("#### Add New Mapping")

        col1, col2 = st.columns(2)

        with col1:
            channel = st.selectbox(
                "Channel",
                options=["ig", "fb", "linkedin", "twitter"],
                format_func=lambda x: {"ig": "Instagram", "fb": "Facebook", "linkedin": "LinkedIn", "twitter": "Twitter"}[x]
            )

        with col2:
            aspect_ratio = st.selectbox(
                "Aspect Ratio",
                options=["1x1", "4x5", "9x16", "16x9"],
                format_func=lambda x: {
                    "1x1": "Square (1:1)",
                    "4x5": "Portrait (4:5)",
                    "9x16": "Story (9:16)",
                    "16x9": "Landscape (16:9)"
                }[x]
            )

        template_id_input = st.text_input(
            "Canva Template ID",
            placeholder="Enter template ID from Canva",
            help="You can find this in the template URL or browse templates in the first tab"
        )

        if st.button("💾 Save Mapping", type="primary"):
            if template_id_input:
                template_key = f"{channel}_{aspect_ratio}"

                # Update tokens
                updated_templates = tokens.templates.copy() if tokens.templates else {}
                updated_templates[template_key] = template_id_input
                tokens.templates = updated_templates

                # Save to Brand Brain
                brand_brain.save_brand_brain(
                    selected_kit.id,
                    tokens=tokens,
                    policies=policies
                )

                st.success(f"✅ Saved mapping for {template_key}")
                st.rerun()
            else:
                st.error("Please enter a template ID")

    # TAB 3: Canva Profile
    with tab3:
        st.markdown("### Your Canva Profile")

        with st.spinner("Loading profile..."):
            profile = renderer.get_user_profile()

        if profile:
            col1, col2 = st.columns([1, 3])

            with col1:
                # Profile photo
                photo = profile.get("photo", {}).get("url")
                if photo:
                    st.image(photo, width=150)

            with col2:
                st.markdown(f"**Name:** {profile.get('display_name', 'N/A')}")
                st.markdown(f"**Email:** {profile.get('email', 'N/A')}")
                st.markdown(f"**User ID:** `{profile.get('id', 'N/A')}`")

                # Team info
                team = profile.get("team")
                if team:
                    st.markdown(f"**Team:** {team.get('name', 'N/A')}")

            st.markdown("---")

            # User designs
            st.markdown("### Recent Designs")

            designs = renderer.list_user_designs(limit=9)

            if designs:
                cols = st.columns(3)

                for idx, design in enumerate(designs):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            thumbnail = design.get("thumbnail", {}).get("url")
                            if thumbnail:
                                st.image(thumbnail, use_container_width=True)

                            st.caption(design.get("title", "Untitled"))

                            if st.button("Open in Canva", key=f"open_design_{design.get('id')}"):
                                edit_url = design.get("urls", {}).get("edit_url")
                                if edit_url:
                                    st.markdown(f"[Open design]({edit_url})")
            else:
                st.info("No designs found")

        else:
            st.error("Failed to load profile. Please try reconnecting.")


if __name__ == "__main__":
    main()
