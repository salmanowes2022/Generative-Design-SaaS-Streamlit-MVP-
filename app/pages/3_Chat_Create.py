"""
Chat-Based Design Creation
Conversational AI interface for creating designs through natural language
"""
import streamlit as st
from uuid import UUID
from datetime import datetime
import io

from app.core.chat_agent_planner import ChatAgentPlanner, DesignPlan
from app.core.brand_brain import brand_brain, BrandTokens, BrandPolicies
from app.core.brandkit import brand_kit_manager
from app.core.design_engine import DesignEngine  # NEW: Use unified design engine
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title="Chat Create",
    page_icon="💬",
    layout="wide"
)

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"

if "user_id" not in st.session_state:
    st.session_state.user_id = "00000000-0000-0000-0000-000000000011"

if "chat_agent" not in st.session_state:
    st.session_state.chat_agent = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_plan" not in st.session_state:
    st.session_state.current_plan = None

if "current_design" not in st.session_state:
    st.session_state.current_design = None


def init_chat_agent():
    """Initialize chat agent with brand context"""
    try:
        # Get brand kits
        org_id = UUID(st.session_state.org_id) if isinstance(st.session_state.org_id, str) else st.session_state.org_id

        brand_kits = brand_kit_manager.get_brand_kits_by_org(org_id)

        if not brand_kits:
            st.error("⚠️ No brand kits found. Please create one first.")
            if st.button("🏁 Create Brand Kit"):
                st.switch_page("pages/1_Onboard_Brand_Kit.py")
            return None

        # Let user select brand kit
        brand_kit_options = {kit.name: kit for kit in brand_kits}

        selected_kit_name = st.sidebar.selectbox(
            "Select Brand Kit",
            options=list(brand_kit_options.keys()),
            key="chat_brand_kit_selector"
        )

        selected_kit = brand_kit_options[selected_kit_name]

        # Load brand brain (OLD format)
        tokens_old, policies = brand_brain.get_brand_brain(selected_kit.id)

        if not tokens_old:
            st.sidebar.error("❌ Brand Brain not configured. Using DEFAULT COLORS (not your brand)!")
            st.sidebar.warning("⚠️ Go to 'Onboard Brand Kit' to set up your brand colors and voice.")
            tokens_old = BrandTokens.get_default_tokens()
            policies = BrandPolicies.get_default_policies()
            logger.warning(f"No brand brain found for kit {selected_kit.id}, using defaults")
        else:
            # Show what was loaded
            logger.info(f"✅ Loaded brand brain: Primary={tokens_old.color.get('primary')}, Voice={policies.voice if policies else 'None'}")

        # Convert to BrandTokensV2 for Modern Renderer
        from app.core.schemas_v2 import BrandTokensV2, ColorPalette, ColorToken
        try:
            # Extract colors from old format and convert to V2
            colors_v2 = ColorPalette(
                primary=ColorToken(hex=tokens_old.color.get('primary', '#4F46E5')),
                secondary=ColorToken(hex=tokens_old.color.get('secondary', '#7C3AED')),
                accent=ColorToken(hex=tokens_old.color.get('accent', '#F59E0B')),
                neutral={},
                semantic=None
            )
            tokens_v2 = BrandTokensV2(
                brand_id=str(selected_kit.id),
                colors=colors_v2
            )
            st.sidebar.success(f"✅ Loaded brand: {selected_kit.name}")
            st.sidebar.caption(f"Colors: {tokens_old.color.get('primary')} / {tokens_old.color.get('accent')}")
        except Exception as e:
            logger.error(f"Error converting tokens: {e}")
            tokens_v2 = BrandTokensV2.get_default_tokens()

        # Create chat agent (uses OLD tokens format)
        agent = ChatAgentPlanner(tokens_old, policies)

        return agent, tokens_v2, policies, selected_kit

    except Exception as e:
        logger.error(f"Error initializing chat agent: {e}")
        st.error(f"Error: {e}")
        return None


def render_chat_interface():
    """Render the chat UI"""
    st.title("💬 Chat Create")
    st.markdown("Create designs through conversation with your AI brand designer")

    # Sidebar - Brand Selection
    st.sidebar.header("🎨 Brand Context")

    init_result = init_chat_agent()
    if not init_result:
        return

    agent, tokens, policies, selected_kit = init_result

    # Save to session state
    st.session_state.chat_agent = agent
    st.session_state.current_tokens = tokens
    st.session_state.current_policies = policies

    # Brand stats - ENHANCED with actual values
    with st.sidebar.expander("📊 Brand Data Loaded", expanded=True):
        # Show actual brand colors
        if hasattr(tokens, 'colors'):
            # BrandTokensV2 format
            st.write("**🎨 Brand Colors:**")
            st.markdown(f"<div style='background:{tokens.colors.primary.hex}; padding:8px; border-radius:4px; margin:4px 0;'><b>Primary:</b> {tokens.colors.primary.hex}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:{tokens.colors.secondary.hex}; padding:8px; border-radius:4px; margin:4px 0;'><b>Secondary:</b> {tokens.colors.secondary.hex}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:{tokens.colors.accent.hex}; padding:8px; border-radius:4px; margin:4px 0;'><b>Accent:</b> {tokens.colors.accent.hex}</div>", unsafe_allow_html=True)
        else:
            # Old BrandTokens format
            st.write("**🎨 Brand Colors:**")
            st.write(f"Primary: {tokens.color.get('primary', 'Not set')}")
            st.write(f"Secondary: {tokens.color.get('secondary', 'Not set')}")
            st.write(f"Accent: {tokens.color.get('accent', 'Not set')}")

        # Voice traits
        if policies and policies.voice:
            st.write("**🗣️ Brand Voice:**")
            voice_traits = policies.voice if isinstance(policies.voice, list) else [policies.voice]
            for trait in voice_traits[:5]:
                st.write(f"  • {trait}")
        else:
            st.warning("⚠️ No brand voice configured")

    # NEW: Show brand assets from brand guidelines
    try:
        from uuid import UUID
        from app.core.brandbook_analyzer import BrandBookAnalyzer
        analyzer = BrandBookAnalyzer()
        org_uuid = UUID(st.session_state.org_id)
        brand_guidelines = analyzer.get_brand_guidelines(org_uuid)

        if brand_guidelines and 'brand_assets' in brand_guidelines:
            with st.sidebar.expander("🎨 Brand Assets Available"):
                brand_assets = brand_guidelines.get('brand_assets', {})

                # Characters
                characters = brand_assets.get('characters', [])
                if characters:
                    st.write(f"**👾 Characters:** {len(characters)}")
                    for char in characters[:3]:
                        st.write(f"  • {char.get('name', 'Unnamed')}: {char.get('personality', '')}")

                # Icons
                icons = brand_assets.get('icons', [])
                if icons:
                    st.write(f"**🔷 Icon Sets:** {len(icons)}")
                    for icon_set in icons[:2]:
                        st.write(f"  • {icon_set.get('category', 'Icons')}: {icon_set.get('style', '')}")

                # Illustrations
                illustrations = brand_assets.get('illustrations', [])
                if illustrations:
                    st.write(f"**🖼️ Illustrations:** {len(illustrations)}")
                    for ill in illustrations[:2]:
                        st.write(f"  • {ill.get('theme', 'Style')}: {ill.get('style', '')}")

                # Patterns
                patterns = brand_assets.get('patterns_textures', [])
                if patterns:
                    st.write(f"**📐 Patterns:** {len(patterns)}")
                    for pattern in patterns[:2]:
                        st.write(f"  • {pattern.get('name', 'Pattern')}")

                if not (characters or icons or illustrations or patterns):
                    st.info("Upload brand book to extract characters, icons, patterns!")
                else:
                    st.success(f"✅ {len(characters) + len(icons) + len(illustrations) + len(patterns)} assets ready!")

                # Store in session for design generation
                st.session_state.brand_guidelines = brand_guidelines

                # Show PBK status
                st.sidebar.markdown("---")
                st.sidebar.success("🚀 **Full Intelligence Mode Active**")
                st.sidebar.caption("AI will use complete brand knowledge from your brand book to create designs")

    except Exception as e:
        logger.debug(f"Could not load brand assets: {e}")
        # Not critical - continue without assets
        st.sidebar.markdown("---")
        st.sidebar.info("🎨 **Template Mode Active**")
        st.sidebar.caption("Upload brand book for full intelligence mode")

    st.sidebar.markdown("---")

    # Chat controls
    if st.sidebar.button("🔄 New Conversation"):
        agent.reset_conversation()
        st.session_state.chat_history = []
        st.session_state.current_plan = None
        st.session_state.current_design = None
        st.rerun()

    if st.sidebar.button("📥 Download Chat Log"):
        chat_log = agent.export_chat_log()
        st.sidebar.download_button(
            "💾 Download",
            chat_log,
            file_name=f"chat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

    # Main chat area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 💬 Conversation")

        # Display chat history
        chat_container = st.container()

        with chat_container:
            # Get history from agent
            history = agent.get_conversation_history()

            for msg in history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("What would you like to create?"):
            # Add user message to display
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get response from agent
            with st.spinner("Thinking..."):
                response = agent.chat(prompt)

            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(response)

            # Try to extract design plan
            plan = agent.extract_design_plan(response)

            if plan:
                st.session_state.current_plan = plan
                st.success("✅ Design plan created! Review in the right panel.")
                st.rerun()

    with col2:
        st.markdown("### 🎨 Design Preview")

        if st.session_state.current_plan:
            plan = st.session_state.current_plan

            # Display plan details
            with st.expander("📋 Design Plan", expanded=True):
                st.write(f"**Headline:** {plan.headline}")
                st.write(f"**Subhead:** {plan.subhead}")
                st.write(f"**CTA:** {plan.cta_text}")
                st.write(f"**Channel:** {plan.channel}")
                st.write(f"**Aspect:** {plan.aspect_ratio}")
                st.write(f"**Palette:** {plan.palette_mode}")

                if plan.reasoning:
                    st.info(f"**Why:** {plan.reasoning}")

            # Generate design button
            if st.button("🚀 Generate Design", type="primary", width="stretch"):
                with st.spinner("Creating your beautiful design..."):
                    try:
                        # NEW: Use HTML/CSS design engine (no DALL-E needed!)
                        st.write("🎨 Using brand colors from your brand book...")

                        # Initialize design engine with brand tokens from session state
                        tokens = st.session_state.current_tokens

                        # DEBUG: PROMINENT color check
                        st.markdown("---")
                        st.markdown("### 🔍 BRAND COLORS LOADED")

                        if hasattr(tokens, 'colors'):
                            primary = tokens.colors.primary.hex
                            secondary = tokens.colors.secondary.hex
                            accent = tokens.colors.accent.hex

                            # Show color boxes
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"<div style='background:{primary}; padding:20px; border-radius:8px; text-align:center; color:white;'><b>Primary</b><br/>{primary}</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"<div style='background:{secondary}; padding:20px; border-radius:8px; text-align:center; color:white;'><b>Secondary</b><br/>{secondary}</div>", unsafe_allow_html=True)
                            with col3:
                                st.markdown(f"<div style='background:{accent}; padding:20px; border-radius:8px; text-align:center; color:white;'><b>Accent</b><br/>{accent}</div>", unsafe_allow_html=True)

                            # Check if using defaults
                            if primary == '#4F46E5' and accent == '#F59E0B':
                                st.error("🚨 USING DEFAULT COLORS! Your brand brain is NOT configured!")
                                st.error("👉 Go to 'Onboard Brand Kit' to set YOUR brand colors!")
                            else:
                                st.success(f"✅ Using YOUR custom brand colors!")
                        else:
                            st.error("❌ No color data found!")

                        st.markdown("---")

                        # Get brand guidelines if available
                        brand_guidelines = None
                        if hasattr(st.session_state, 'brand_guidelines'):
                            brand_guidelines = st.session_state.brand_guidelines
                            if brand_guidelines and 'brand_assets' in brand_guidelines:
                                st.info("🎨 Using brand assets from your brand book (characters, icons, patterns)")

                        engine = DesignEngine(tokens, use_html=True, brand_guidelines=brand_guidelines)

                        # Show renderer info
                        renderer_info = engine.get_renderer_info()
                        if renderer_info['type'] == 'HTML/CSS':
                            st.info(f"✨ Using {renderer_info['type']} renderer with {renderer_info['templates']} beautiful templates")
                        else:
                            st.info(f"✨ Using {renderer_info['type']} renderer (gradient backgrounds + brand colors)")
                            st.caption("💡 Install Playwright for even better HTML/CSS designs: `pip install playwright && playwright install chromium`")

                        # Get logo from brand assets
                        logo_url = None
                        try:
                            from app.core.brandkit import brand_kit_manager
                            assets = brand_kit_manager.get_brand_assets(selected_kit.id)
                            st.write(f"🔍 DEBUG - Found {len(assets)} brand assets")

                            # Find logo asset
                            for asset in assets:
                                st.write(f"  - Asset: {asset.type} - {asset.url[:50] if asset.url else 'No URL'}...")
                                if asset.type == 'logo':
                                    logo_url = asset.url
                                    st.success(f"✅ Found logo: {logo_url[:80]}...")
                                    logger.info(f"Found logo: {logo_url}")
                                    break

                            if not logo_url:
                                st.warning("⚠️ No logo found in brand assets. Upload one in 'Onboard Brand Kit' page.")
                        except Exception as e:
                            st.error(f"❌ Error loading logo: {e}")
                            logger.warning(f"Could not load logo: {e}")

                        # Generate 3 design variations
                        st.write("🎨 Generating 3 beautiful design variations...")

                        # Create 3 variations with different palette modes
                        palette_variations = ['primary', 'secondary', 'vibrant']
                        design_variations = []

                        for i, palette_mode in enumerate(palette_variations, 1):
                            st.write(f"  🎨 Variation {i}: {palette_mode.title()} colors...")

                            # Update plan with different palette mode
                            plan_variation = DesignPlan(
                                headline=plan.headline,
                                subhead=plan.subhead,
                                cta_text=plan.cta_text,
                                channel=plan.channel,
                                aspect_ratio=plan.aspect_ratio,
                                palette_mode=palette_mode,
                                background_style=plan.background_style,
                                visual_concept=plan.visual_concept,
                                logo_position=plan.logo_position,
                                reasoning=plan.reasoning
                            )

                            result = engine.generate_design(
                                plan=plan_variation,
                                background_url=None,
                                logo_url=logo_url,
                                product_image_url=None,
                                validate_quality=True
                            )

                            design_variations.append({
                                'image': result['image'],
                                'quality_score': result['quality_score'],
                                'suggestions': result['suggestions'],
                                'palette_mode': palette_mode
                            })

                        st.success(f"✅ Generated {len(design_variations)} design variations!")

                        # Display all 3 design variations
                        st.markdown("### 🎨 Choose Your Favorite Design")

                        cols = st.columns(3)
                        selected_variation = None

                        for idx, (col, variation) in enumerate(zip(cols, design_variations)):
                            with col:
                                st.image(variation['image'], use_container_width=True)
                                st.caption(f"**{variation['palette_mode'].title()} Colors**")
                                st.caption(f"Score: {variation['quality_score']}/100")

                                if st.button(f"✅ Use This", key=f"select_design_{idx}"):
                                    selected_variation = idx

                        # Use selected design or default to first
                        if selected_variation is None:
                            selected_variation = 0

                        design_image = design_variations[selected_variation]['image']
                        quality_score = design_variations[selected_variation]['quality_score']
                        suggestions = design_variations[selected_variation]['suggestions']

                        st.markdown("---")
                        st.write(f"**Selected:** {design_variations[selected_variation]['palette_mode'].title()} variation")

                        # Show quality score
                        if quality_score:
                            st.metric("Quality Score", f"{quality_score}/100")
                            if quality_score >= 90:
                                st.success("🌟 Excellent quality!")
                            elif quality_score >= 75:
                                st.info("👍 Good quality!")
                            else:
                                st.warning("💡 Could be improved")

                        # Show suggestions
                        if suggestions:
                            with st.expander("💡 Improvement Suggestions"):
                                for suggestion in suggestions:
                                    st.write(f"• {suggestion}")

                        # Save design to storage
                        st.write("💾 Saving design...")
                        from app.core.storage import storage
                        from PIL import Image
                        import io

                        # Convert PIL Image to bytes
                        img_byte_arr = io.BytesIO()
                        design_image.save(img_byte_arr, format='PNG')
                        img_byte_arr.seek(0)

                        # Upload to storage
                        filename = f"chat_design_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        file_path = f"{st.session_state.org_id}/chat_designs/{filename}"
                        design_url = storage.upload_file(
                            bucket_type="assets",
                            file_path=file_path,
                            file_data=img_byte_arr,
                            content_type="image/png"
                        )

                        # Save to database (design library)
                        try:
                            from app.infra.db import db
                            import json

                            # Get brand kit ID if available
                            brand_kit_id = None
                            if hasattr(st.session_state, 'brand_kit') and st.session_state.brand_kit:
                                brand_kit_id = st.session_state.brand_kit.id

                            # Save to assets table (design library)
                            db.execute("""
                                INSERT INTO assets (
                                    org_id,
                                    brand_kit_id,
                                    url,
                                    design_plan,
                                    quality_score,
                                    generation_metadata,
                                    created_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                            """, (
                                str(st.session_state.org_id),
                                str(brand_kit_id) if brand_kit_id else None,
                                design_url,
                                json.dumps({
                                    'headline': plan.headline,
                                    'subhead': plan.subhead,
                                    'cta_text': plan.cta_text,
                                    'channel': plan.channel,
                                    'aspect_ratio': plan.aspect_ratio,
                                    'palette_mode': design_variations[selected_variation]['palette_mode']
                                }),
                                quality_score,
                                json.dumps({
                                    'mode': 'pbk_intelligence' if st.session_state.get('brand_guidelines') else 'template',
                                    'created_from': 'chat_interface',
                                    'variations_generated': len(design_variations)
                                })
                            ))

                            logger.info(f"✅ Design saved to library: {file_path}")

                        except Exception as db_error:
                            logger.warning(f"Could not save to design library: {db_error}")
                            # Don't block the user if database save fails

                        # Save image and URL to session state
                        st.session_state.current_design_image = design_image
                        st.session_state.current_design = design_url
                        st.session_state.current_quality = quality_score

                        st.success("🎉 Beautiful design created and saved to your library!")
                        st.rerun()

                    except Exception as e:
                        logger.error(f"Design generation failed: {e}")
                        st.error(f"Error: {e}")

            # Show current design
            if st.session_state.current_design:
                st.markdown("---")
                st.markdown("### ✨ Your Design")

                # Show quality score if available
                if hasattr(st.session_state, 'current_quality') and st.session_state.current_quality:
                    col_q1, col_q2 = st.columns(2)
                    with col_q1:
                        st.metric("Quality Score", f"{st.session_state.current_quality}/100")
                    with col_q2:
                        if st.session_state.current_quality >= 90:
                            st.success("🌟 Excellent!")
                        elif st.session_state.current_quality >= 75:
                            st.info("👍 Good!")
                        else:
                            st.warning("💡 Can improve")

                # Display the actual image, not the URL
                if hasattr(st.session_state, 'current_design_image') and st.session_state.current_design_image:
                    st.image(st.session_state.current_design_image, use_container_width=True)
                else:
                    st.image(st.session_state.current_design, use_container_width=True)

                # Download button
                if hasattr(st.session_state, 'current_design_image'):
                    # Convert image to bytes for download
                    import io
                    img_byte_arr = io.BytesIO()
                    st.session_state.current_design_image.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)

                    st.download_button(
                        "📥 Download PNG",
                        data=img_byte_arr.getvalue(),
                        file_name=f"design_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                        mime="image/png",
                        width="stretch"
                    )

                # Iterate button
                if st.button("🔄 Refine Design", width="stretch"):
                    st.info("💬 Tell me what you'd like to change in the chat!")

        else:
            st.info("👋 Start a conversation to create a design!")

            # Quick start examples
            st.markdown("#### 💡 Try These:")

            example_prompts = [
                "Create a Black Friday Instagram post",
                "Make a LinkedIn announcement for our new product launch",
                "Design a Facebook ad for our summer sale",
                "Create an Instagram story for a webinar"
            ]

            for prompt in example_prompts:
                if st.button(prompt, width="stretch"):
                    # Simulate user input
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    response = agent.chat(prompt)

                    with st.chat_message("assistant"):
                        st.markdown(response)

                    plan = agent.extract_design_plan(response)
                    if plan:
                        st.session_state.current_plan = plan

                    st.rerun()


def main():
    """Main function"""
    render_chat_interface()


if __name__ == "__main__":
    main()
