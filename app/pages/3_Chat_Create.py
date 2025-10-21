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
from app.core.gen_openai import image_generator
from app.core.schemas import JobCreate, JobParams, AspectRatio
from app.core.renderer_grid import GridRenderer
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

        # Load brand brain
        tokens, policies = brand_brain.get_brand_brain(selected_kit.id)

        if not tokens:
            st.sidebar.warning("⚠️ Brand Brain not configured. Using defaults.")
            tokens = BrandTokens.get_default_tokens()
            policies = BrandPolicies.get_default_policies()

        # Create chat agent
        agent = ChatAgentPlanner(tokens, policies)

        return agent, tokens, policies, selected_kit

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

    # Brand stats
    with st.sidebar.expander("📊 Brand Stats"):
        st.write(f"**Colors:** {len([c for c in [tokens.color.get('primary'), tokens.color.get('secondary')] if c])}")
        st.write(f"**Approved CTAs:** {len(tokens.cta_whitelist)}")
        if policies and policies.voice:
            # Handle both list and string types
            voice_traits = policies.voice if isinstance(policies.voice, list) else [policies.voice]
            st.write(f"**Voice Traits:** {', '.join(voice_traits[:3])}")

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
            if st.button("🚀 Generate Design", type="primary", use_container_width=True):
                with st.spinner("Creating your design..."):
                    try:
                        # Step 1: Generate background image
                        st.write("1️⃣ Generating AI background...")

                        # Map aspect ratio string to enum
                        aspect_map = {
                            "1x1": AspectRatio.SQUARE,
                            "4x5": AspectRatio.PORTRAIT,
                            "9x16": AspectRatio.STORY
                        }
                        aspect_enum = aspect_map.get(plan.aspect_ratio, AspectRatio.SQUARE)

                        # Create proper JobCreate object
                        job_data = JobCreate(
                            prompt=plan.background_style,
                            engine="dall-e-3",
                            params=JobParams(
                                aspect_ratio=aspect_enum,
                                num_images=1,
                                quality="hd",
                                style="vivid"
                            )
                        )

                        # Use the singleton image_generator instance
                        gen_result = image_generator.generate_with_moderation(
                            org_id=UUID(st.session_state.org_id),
                            job_data=job_data
                        )

                        if not gen_result or not gen_result.get("assets"):
                            st.error("Failed to generate background image")
                            return

                        # Extract first asset URL (assets are objects with base_url attribute)
                        bg_url = gen_result["assets"][0].base_url
                        if not bg_url:
                            st.error("No image URL returned")
                            return

                        # Step 2: Render design
                        st.write("2️⃣ Composing layout...")
                        renderer = GridRenderer(tokens)

                        # Get logo from brand assets
                        logo_url = None
                        try:
                            from app.core.brandkit import brand_asset_manager
                            assets = brand_asset_manager.get_assets_by_brand_kit(selected_kit.id)
                            # Find logo asset
                            for asset in assets:
                                if asset.type == 'logo':
                                    logo_url = asset.url
                                    logger.info(f"Found logo: {logo_url}")
                                    break
                        except Exception as e:
                            logger.warning(f"Could not load logo: {e}")

                        design_image = renderer.render_design(
                            plan=plan,
                            background_url=bg_url,
                            logo_url=logo_url,
                            product_image_url=None
                        )

                        # Step 3: Save design
                        st.write("3️⃣ Saving design...")
                        design_url = renderer.save_design(
                            design_image,
                            org_id=str(st.session_state.org_id),
                            filename=f"chat_design_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        )

                        st.session_state.current_design = design_url

                        st.success("🎉 Design created!")
                        st.rerun()

                    except Exception as e:
                        logger.error(f"Design generation failed: {e}")
                        st.error(f"Error: {e}")

            # Show current design
            if st.session_state.current_design:
                st.markdown("---")
                st.markdown("### ✨ Your Design")
                st.image(st.session_state.current_design, use_container_width=True)

                # Download button
                st.download_button(
                    "📥 Download PNG",
                    data=st.session_state.current_design,
                    file_name=f"design_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )

                # Iterate button
                if st.button("🔄 Refine Design", use_container_width=True):
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
                if st.button(prompt, use_container_width=True):
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
