"""
Generate Page v2
Chat to Plan → AI Background → Canva Composition
Non-hybrid UX: User gets finished design directly from Canva
"""
import streamlit as st
import json
from app.core.schemas import AspectRatio
from app.core.brandkit import brand_kit_manager
from app.core.brand_brain import brand_brain
from app.core.planner_v2 import planner_v2
from app.core.gen_openai import image_generator
from app.core.ocr_validator import ocr_validator
from app.core.logo_engine import logo_engine
from app.core.renderer_canva import CanvaRenderer
from app.core.canva_oauth_bridge import canva_oauth_bridge, render_canva_auth_button
from app.core.validator_v2 import validator_v2
from app.infra.billing import billing_manager
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Generate Assets v2", page_icon="🎨", layout="wide")

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"

if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_plan" not in st.session_state:
    st.session_state.current_plan = None

if "current_design" not in st.session_state:
    st.session_state.current_design = None


def main():
    st.title("🎨 AI Design Studio v2")
    st.markdown("**Chat → Plan → Create** - Powered by Brand Brain")

    # Brand kit selection
    st.sidebar.header("⚙️ Settings")

    # Canva connection status
    st.sidebar.markdown("### 🔗 Canva")
    render_canva_auth_button()
    st.sidebar.markdown("---")

    try:
        brand_kits = brand_kit_manager.get_brand_kits_by_org(st.session_state.org_id)

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
            help="Active brand context for AI generation"
        )

        selected_kit = brand_kit_options[selected_kit_name]

        # Load Brand Brain
        brain_data = brand_brain.get_brand_brain(selected_kit.id)

        if not brain_data:
            st.sidebar.warning("⚠️ Brand Brain not configured. Using defaults.")
            tokens = brand_brain.BrandTokens.get_default_tokens()
            policies = None
        else:
            tokens = brain_data["tokens"]
            policies = brain_data["policies"]

        # Show brand stats
        with st.sidebar.expander("📊 Brand Stats"):
            st.write(f"**Colors:** {len([c for c in [tokens.color.get('primary'), tokens.color.get('secondary')] if c])}")
            st.write(f"**Templates:** {len(tokens.templates)}")
            st.write(f"**CTA Options:** {len(tokens.cta_whitelist)}")
            if policies:
                st.write(f"**Voice Traits:** {len(policies.voice)}")

    except Exception as e:
        logger.error(f"Error loading brand kits: {str(e)}")
        st.error("Error loading brand kits")
        return

    # Channel selector
    channel = st.sidebar.selectbox(
        "Target Channel",
        options=["ig", "fb", "linkedin", "twitter"],
        format_func=lambda x: {"ig": "Instagram", "fb": "Facebook", "linkedin": "LinkedIn", "twitter": "Twitter"}[x]
    )

    # Usage meter
    try:
        usage = billing_manager.get_current_usage(st.session_state.org_id)
        st.sidebar.metric("Credits", f"{usage['credits_remaining']}/{usage['monthly_credits']}")

        if usage["credits_remaining"] < 50:
            st.sidebar.warning("⚠️ Low credits")
    except Exception as e:
        logger.error(f"Error loading usage: {str(e)}")

    st.sidebar.markdown("---")

    # Main workflow tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📋 Plan", "🎨 Design"])

    # TAB 1: Chat to Plan
    with tab1:
        st.markdown("### Tell me what you need")
        st.caption("I'll create a design plan based on your brand guidelines")

        # Chat interface
        user_message = st.text_area(
            "Message",
            placeholder="Create an Instagram post promoting our new product launch with an energetic, modern vibe",
            height=100,
            key="chat_input"
        )

        col1, col2 = st.columns([1, 4])

        with col1:
            if st.button("📤 Send", use_container_width=True):
                if user_message and len(user_message) >= 10:
                    with st.spinner("🧠 Brand Brain is thinking..."):
                        # Create plan
                        result = planner_v2.chat_to_plan(
                            user_message,
                            tokens,
                            policies,
                            context={"channel": channel}
                        )

                        if result["success"]:
                            st.session_state.current_plan = result["plan"]
                            st.session_state.chat_history.append({
                                "user": user_message,
                                "plan": result["plan"],
                                "reasoning": result["reasoning"],
                                "warnings": result["warnings"]
                            })
                            st.success("✅ Plan created! Check the Plan tab")
                            st.rerun()
                        else:
                            st.error(f"❌ Planning failed: {result.get('error')}")
                else:
                    st.error("Please provide a detailed message (at least 10 characters)")

        with col2:
            if st.button("🔄 Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.session_state.current_plan = None
                st.rerun()

        # Show chat history
        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown("### Recent Conversations")

            for idx, conv in enumerate(reversed(st.session_state.chat_history[-3:])):
                with st.expander(f"💬 {conv['user'][:60]}...", expanded=(idx == 0)):
                    st.markdown(f"**You:** {conv['user']}")
                    st.markdown(f"**Brand Brain:** {conv['reasoning']}")

                    if conv.get("warnings"):
                        st.warning("⚠️ Warnings:\n" + "\n".join(f"- {w}" for w in conv["warnings"]))

                    st.json(conv["plan"])

    # TAB 2: Plan Review & Edit
    with tab2:
        if not st.session_state.current_plan:
            st.info("👈 Start a conversation in the Chat tab to create a plan")
            return

        plan = st.session_state.current_plan

        st.markdown("### Design Plan")
        st.caption("Review and refine before creating")

        # Editable plan fields
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Content**")
            headline = st.text_input(
                "Headline (max 7 words)",
                value=plan.get("headline", ""),
                max_chars=50,
                help="Short, punchy headline"
            )

            subhead = st.text_area(
                "Subhead (max 16 words)",
                value=plan.get("subhead", ""),
                max_chars=120,
                height=80,
                help="Supporting detail"
            )

            cta_text = st.selectbox(
                "Call-to-Action",
                options=tokens.cta_whitelist,
                index=tokens.cta_whitelist.index(plan.get("cta_text", tokens.cta_whitelist[0])) if plan.get("cta_text") in tokens.cta_whitelist else 0
            )

        with col_b:
            st.markdown("**Visual**")
            visual_concept = st.text_area(
                "Visual Concept",
                value=plan.get("visual_concept", ""),
                height=100,
                help="What the AI should generate"
            )

            aspect_ratio = st.selectbox(
                "Aspect Ratio",
                options=["1x1", "4x5", "9x16", "16x9"],
                index=["1x1", "4x5", "9x16", "16x9"].index(plan.get("aspect_ratio", "1x1"))
            )

            palette_mode = st.selectbox(
                "Color Palette",
                options=["primary", "secondary", "accent", "mono"],
                index=["primary", "secondary", "accent", "mono"].index(plan.get("palette_mode", "primary"))
            )

            logo_position = st.selectbox(
                "Logo Position",
                options=tokens.logo.get("allowed_positions", ["top-right"]),
                index=0
            )

        # Update plan button
        if st.button("💾 Update Plan", use_container_width=True):
            st.session_state.current_plan = {
                "headline": headline,
                "subhead": subhead,
                "cta_text": cta_text,
                "visual_concept": visual_concept,
                "channel": plan.get("channel", channel),
                "aspect_ratio": aspect_ratio,
                "palette_mode": palette_mode,
                "background_style": plan.get("background_style", visual_concept),
                "logo_position": logo_position
            }
            st.success("✅ Plan updated")
            st.rerun()

        # Validate plan
        st.markdown("---")
        warnings = planner_v2._validate_plan(st.session_state.current_plan, tokens, policies)

        if warnings:
            st.error("❌ Plan has issues:")
            for warning in warnings:
                st.warning(f"- {warning}")
        else:
            st.success("✅ Plan is valid and ready to create")

        # Create button
        st.markdown("---")

        if st.button("🚀 Create Design in Canva", type="primary", use_container_width=True):
            if warnings:
                st.error("Please fix plan issues before creating")
                return

            with st.status("🎨 Creating your design...", expanded=True) as status:
                try:
                    # Step 1: Generate background with OCR gate
                    st.write("1️⃣ Generating AI background...")

                    from app.core.prompt_builder_v2 import prompt_builder_v2

                    background_prompt = prompt_builder_v2.build_background_prompt(
                        user_request=st.session_state.current_plan["visual_concept"],
                        tokens=tokens,
                        aspect_ratio=st.session_state.current_plan["aspect_ratio"],
                        logo_position=st.session_state.current_plan["logo_position"]
                    )

                    # Generate with OCR validation
                    max_attempts = 3
                    background_url = None

                    for attempt in range(max_attempts):
                        st.write(f"   Attempt {attempt + 1}/{max_attempts}...")

                        # Generate image
                        from app.core.schemas import JobCreate, JobParams
                        job_data = JobCreate(
                            prompt=background_prompt,
                            engine="dall-e-3",
                            params=JobParams(
                                aspect_ratio=AspectRatio.SQUARE,  # Map aspect_ratio string to enum
                                num_images=1,
                                quality="hd",
                                style="vivid"
                            )
                        )

                        gen_result = image_generator.generate_with_moderation(
                            st.session_state.org_id,
                            job_data
                        )

                        candidate_url = gen_result["assets"][0].base_url

                        # OCR check
                        ocr_result = ocr_validator.validate_background(candidate_url)

                        if ocr_result["passed"]:
                            background_url = candidate_url
                            st.write("   ✅ Background passed OCR check")
                            break
                        else:
                            st.write(f"   ⚠️ Text detected: '{ocr_result['detected_text']}', regenerating...")

                    if not background_url:
                        raise ValueError("Failed to generate clean background after 3 attempts")

                    # Step 2: Create design in Canva
                    st.write("2️⃣ Creating design in Canva...")

                    # Check Canva authentication
                    if not canva_oauth_bridge.is_authenticated():
                        raise ValueError("Please connect to Canva first (see sidebar)")

                    # Get access token
                    access_token = canva_oauth_bridge.get_access_token()
                    if not access_token:
                        raise ValueError("Failed to get Canva access token. Please reconnect.")

                    # Initialize renderer with token
                    canva_renderer = CanvaRenderer(access_token=access_token)

                    # Get template ID
                    template_key = f"{st.session_state.current_plan['channel']}_{st.session_state.current_plan['aspect_ratio']}"
                    template_id = tokens.templates.get(template_key)

                    if not template_id:
                        st.warning(f"No template for {template_key}. Configure templates in the Canva Templates page.")
                        raise ValueError(f"No template configured for {template_key}")

                    # Prepare content
                    content = {
                        "headline": st.session_state.current_plan["headline"],
                        "subhead": st.session_state.current_plan["subhead"],
                        "cta_text": st.session_state.current_plan["cta_text"],
                        "bg_image_url": background_url,
                        "palette_mode": st.session_state.current_plan["palette_mode"]
                    }

                    # Create in Canva
                    canva_result = canva_renderer.create_design(
                        template_id=template_id,
                        content=content,
                        tokens=tokens,
                        org_id=st.session_state.org_id
                    )

                    if not canva_result["success"]:
                        raise ValueError(f"Canva creation failed: {canva_result.get('error')}")

                    st.write("   ✅ Design created in Canva")

                    # Step 3: Validate
                    st.write("3️⃣ Validating brand compliance...")

                    validation_result = validator_v2.validate_asset(
                        image_url=canva_result["export_url"],
                        tokens=tokens,
                        policies=policies,
                        text_on_image=f"{st.session_state.current_plan['headline']} {st.session_state.current_plan['subhead']}"
                    )

                    # Store result
                    st.session_state.current_design = {
                        "canva_result": canva_result,
                        "validation": validation_result,
                        "plan": st.session_state.current_plan
                    }

                    status.update(label="✅ Design complete!", state="complete")
                    st.success("🎉 Your design is ready!")
                    st.balloons()

                    # Switch to Design tab
                    st.rerun()

                except Exception as e:
                    logger.error(f"Design creation error: {str(e)}")
                    status.update(label="❌ Creation failed", state="error")
                    st.error(f"Error: {str(e)}")

                    import traceback
                    with st.expander("🔍 Technical details"):
                        st.code(traceback.format_exc())

    # TAB 3: Final Design & Validation
    with tab3:
        if not st.session_state.current_design:
            st.info("👈 Create a design in the Plan tab to see results")
            return

        design = st.session_state.current_design
        canva_result = design["canva_result"]
        validation = design["validation"]

        st.markdown("### Your Design")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Show design
            st.image(canva_result["export_url"], use_container_width=True)

            # Actions
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                if st.button("📝 Edit in Canva", use_container_width=True):
                    st.markdown(f"[Open in Canva]({canva_result['design_url']})")

            with col_b:
                if st.button("💾 Download", use_container_width=True):
                    st.markdown(f"[Download PNG]({canva_result['export_url']})")

            with col_c:
                if st.button("🔄 Create New", use_container_width=True):
                    st.session_state.current_plan = None
                    st.session_state.current_design = None
                    st.rerun()

        with col2:
            # Validation panel
            st.markdown("### Brand Compliance")

            score = validation["on_brand_score"]

            # Score display
            if score >= 90:
                score_color = "🟢"
                score_text = "Excellent"
            elif score >= 70:
                score_color = "🟡"
                score_text = "Good"
            else:
                score_color = "🔴"
                score_text = "Needs Work"

            st.metric("On-Brand Score", f"{score}/100", delta=score_text)
            st.markdown(f"{score_color} {score_text}")

            # Detailed validation
            with st.expander("🎨 Color Validation"):
                color_val = validation["color_validation"]
                st.metric("Score", f"{color_val['score']}/100")
                st.write(f"**Avg ΔE:** {color_val.get('avg_delta_e', 'N/A')}")

                if color_val.get("color_matches"):
                    st.caption("Color Matches:")
                    for match in color_val["color_matches"][:3]:
                        st.write(f"- {match['image_color']} → {match['brand_color']} (ΔE: {match['delta_e']:.1f}, {match['match_quality']})")

            with st.expander("📊 Contrast Validation"):
                contrast_val = validation["contrast_validation"]
                st.metric("Score", f"{contrast_val['score']}/100")

                if contrast_val.get("meets_wcag_aa"):
                    st.success("✅ Meets WCAG AA")
                else:
                    st.warning("⚠️ Below WCAG AA")

                if contrast_val.get("ratios"):
                    for ratio in contrast_val["ratios"][:2]:
                        st.write(f"- {ratio['ratio']:.1f}:1 on {ratio['background']}")

            with st.expander("📝 Policy Validation"):
                policy_val = validation["policy_validation"]
                st.metric("Score", f"{policy_val['score']}/100")

                if policy_val.get("violations"):
                    for violation in policy_val["violations"]:
                        st.warning(f"- {violation}")
                else:
                    st.success("✅ No policy violations")

            # Reasons & Suggestions
            if validation.get("reasons"):
                st.markdown("**Issues:**")
                for reason in validation["reasons"]:
                    st.caption(f"- {reason}")

            if validation.get("suggestions"):
                st.markdown("**Suggestions:**")
                for suggestion in validation["suggestions"]:
                    st.caption(f"💡 {suggestion}")


if __name__ == "__main__":
    main()
