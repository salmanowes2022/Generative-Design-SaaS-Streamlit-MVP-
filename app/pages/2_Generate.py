"""
Generate Page
Create AI-generated images with brand context
"""
import streamlit as st
from app.core.schemas import JobCreate, JobParams, AspectRatio
from app.core.router import router
from app.core.brandkit import brand_kit_manager
from app.infra.billing import billing_manager
from app.infra.logging import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Generate Assets", page_icon="🎨", layout="wide")

# Initialize session state
if "org_id" not in st.session_state:
    st.session_state.org_id = "00000000-0000-0000-0000-000000000001"

if "generated_assets" not in st.session_state:
    st.session_state.generated_assets = []


def main():
    st.title("🎨 Generate AI Assets")
    st.markdown("Create stunning images powered by DALL-E 3")
    
    # Check usage
    try:
        usage = billing_manager.get_current_usage(st.session_state.org_id)
        
        # Usage meter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Credits Remaining",
                usage["credits_remaining"],
                delta=f"{usage['monthly_credits']} total"
            )
        
        with col2:
            st.metric(
                "Credits Used",
                usage["credits_used"]
            )
        
        with col3:
            usage_pct = (usage["credits_used"] / usage["monthly_credits"]) * 100 if usage["monthly_credits"] > 0 else 0
            st.metric(
                "Usage",
                f"{usage_pct:.1f}%"
            )
        
        # Warning if low credits
        if usage["credits_remaining"] < 50:
            st.warning("⚠️ Low credits! Consider upgrading your plan.")
        
        if usage["credits_remaining"] == 0:
            st.error("❌ No credits remaining. Please upgrade your plan to continue generating.")
            if st.button("💳 Upgrade Plan"):
                st.switch_page("pages/5_Billing.py")
            return
    
    except Exception as e:
        logger.error(f"Error loading usage: {str(e)}")
        st.error("Error loading credit balance")
    
    st.markdown("---")
    
    # Brand kit selection
    st.subheader("1️⃣ Select Brand Kit")
    
    try:
        brand_kits = brand_kit_manager.get_brand_kits_by_org(st.session_state.org_id)
        
        if not brand_kits:
            st.warning("⚠️ No brand kits found. Please create one first.")
            if st.button("🏁 Create Brand Kit"):
                st.switch_page("pages/1_Onboard_Brand_Kit.py")
            return
        
        # Brand kit selector
        brand_kit_options = {kit.name: kit for kit in brand_kits}
        selected_kit_name = st.selectbox(
            "Choose a brand kit",
            options=list(brand_kit_options.keys()),
            help="The selected brand kit will influence the AI generation"
        )
        
        selected_kit = brand_kit_options[selected_kit_name]
        
        # Show brand kit preview
        with st.expander("🎨 Brand Kit Details"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Colors**")
                st.color_picker("Primary", selected_kit.colors.primary, disabled=True, key="preview_primary")
                if selected_kit.colors.secondary:
                    st.color_picker("Secondary", selected_kit.colors.secondary, disabled=True, key="preview_secondary")
            
            with col_b:
                st.markdown("**Style**")
                st.write(", ".join(selected_kit.style.descriptors))
                if selected_kit.style.voice:
                    st.write(f"Voice: {selected_kit.style.voice}")
    
    except Exception as e:
        logger.error(f"Error loading brand kits: {str(e)}")
        st.error("Error loading brand kits")
        return
    
    # Generation form
    st.markdown("---")
    st.subheader("2️⃣ Describe Your Vision")
    
    with st.form("generation_form"):
        # Prompt input
        user_prompt = st.text_area(
            "What do you want to create?",
            placeholder="A modern office workspace with natural lighting, laptop on desk, coffee cup, minimalist design",
            height=100,
            help="Describe the scene or subject you want to generate. Be specific about composition, mood, and details."
        )
        
        # Generation parameters
        col_param1, col_param2, col_param3 = st.columns(3)
        
        with col_param1:
            aspect_ratio = st.selectbox(
                "Aspect Ratio",
                options=[
                    ("Square (1:1)", AspectRatio.SQUARE),
                    ("Portrait (4:5)", AspectRatio.PORTRAIT),
                    ("Story (9:16)", AspectRatio.STORY)
                ],
                format_func=lambda x: x[0],
                help="Choose the format for your image"
            )[1]
        
        with col_param2:
            num_images = st.slider(
                "Number of Variations",
                min_value=1,
                max_value=4,
                value=3,
                help="Generate multiple variations to choose from"
            )
        
        with col_param3:
            quality = st.selectbox(
                "Quality",
                options=["standard", "hd"],
                help="HD quality uses more credits but provides better results"
            )
        
        # Style preset
        style = st.selectbox(
            "AI Style",
            options=["vivid", "natural"],
            help="Vivid: More dramatic, saturated. Natural: More realistic, subtle."
        )
        
        # Cost calculator
        credits_needed = billing_manager.credits_per_generation * num_images
        st.info(f"💳 This generation will cost **{credits_needed} credits** ({num_images} images × {billing_manager.credits_per_generation} credits)")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Generate Images", use_container_width=True)
        
        if submitted:
            # Validation
            if not user_prompt or len(user_prompt) < 10:
                st.error("❌ Please provide a more detailed prompt (at least 10 characters)")
                return
            
            # Check credits
            if not billing_manager.check_credits_available(st.session_state.org_id, credits_needed):
                st.error(f"❌ Insufficient credits. You need {credits_needed} credits but only have {usage['credits_remaining']} remaining.")
                return
            
            try:
                with st.spinner("🎨 Creating your images with AI... This may take 30-60 seconds..."):
                    # Create job
                    job_data = JobCreate(
                        prompt=user_prompt,
                        engine="dall-e-3",
                        params=JobParams(
                            aspect_ratio=aspect_ratio,
                            num_images=num_images,
                            quality=quality,
                            style=style
                        )
                    )
                    
                    # Generate with workflow
                    result = router.generate_assets_workflow(
                        org_id=st.session_state.org_id,
                        brand_kit_id=selected_kit.id,
                        user_prompt=user_prompt,
                        job_data=job_data
                    )
                    
                    # Store in session state
                    st.session_state.generated_assets = result["assets"]
                    st.session_state.current_job_id = result["job"].id
                    st.session_state.selected_brand_kit_id = str(selected_kit.id)
                    
                    st.success(f"✅ Generated {len(result['assets'])} images successfully!")
                    st.balloons()
                    
                    # Show moderation check
                    if result["moderation"]["safe"]:
                        st.success("✅ Content passed moderation check")
                    
                    st.info(f"💳 {result['credits_used']} credits deducted. Remaining: {usage['credits_remaining'] - result['credits_used']}")
            
            except Exception as e:
                logger.error(f"Error generating images: {str(e)}")
                st.error(f"❌ Generation failed: {str(e)}")
                return
    
    # Display generated images
    if st.session_state.generated_assets:
        st.markdown("---")
        st.subheader("3️⃣ Generated Images")
        st.markdown("Select an image to compose with your brand elements")
        
        # Display in grid
        cols = st.columns(min(len(st.session_state.generated_assets), 3))
        
        for idx, asset in enumerate(st.session_state.generated_assets):
            with cols[idx % 3]:
                st.image(asset.base_url, use_container_width=True)
                
                if st.button(f"✨ Compose This Image", key=f"compose_{asset.id}", use_container_width=True):
                    st.session_state.selected_asset_id = str(asset.id)
                    st.switch_page("pages/3_Compose_Validate.py")
    
    # Prompt tips
    st.markdown("---")
    with st.expander("💡 Prompt Writing Tips"):
        st.markdown("""
        **Great prompts include:**
        - **Subject**: What's the main focus? (e.g., "laptop on desk", "coffee cup")
        - **Setting**: Where is this? (e.g., "modern office", "outdoor cafe")
        - **Mood**: What feeling? (e.g., "energetic", "calm", "professional")
        - **Lighting**: What kind? (e.g., "natural lighting", "golden hour", "studio lighting")
        - **Composition**: How arranged? (e.g., "centered", "minimal background", "lots of negative space")
        
        **Examples:**
        - ✅ "Modern workspace with MacBook on wooden desk, coffee cup, natural window light, minimalist aesthetic, calm morning mood"
        - ✅ "Person working on laptop in cozy cafe, warm ambient lighting, shallow depth of field, professional but relaxed"
        - ❌ "desk" (too simple)
        - ❌ "create an amazing image" (not specific enough)
        
        **Remember:**
        - The AI will NOT add logos or text - that happens in the Compose step
        - Be descriptive but natural - write like you're describing to a photographer
        - Your brand kit's colors and style will influence the generation
        """)


if __name__ == "__main__":
    main()