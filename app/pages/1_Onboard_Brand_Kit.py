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

    # Brand Book Upload Section (PRIORITY!)
    st.markdown("## 📖 Upload Brand Book (PDF)")
    st.info("""
    **📚 Upload your complete brand guidelines!**

    Upload your brand book PDF and the AI will extract EVERYTHING:
    - **Visual Identity**: Logo variations, colors (with HEX codes), typography
    - **Brand Messaging**: Voice, tone, values, personality
    - **Imagery Guidelines**: Photography style, composition rules
    - **Layout System**: Grid, spacing, composition principles
    - **Design Patterns**: Visual elements, graphic devices
    - **Usage Rules**: Do's and Don'ts, application examples

    **This creates a complete knowledge base for the AI to follow!**
    """)

    with st.expander("📤 Upload Brand Book PDF", expanded=True):
        st.markdown("### Upload Your Brand Guidelines PDF")

        brand_book_file = st.file_uploader(
            "Select your brand book PDF",
            type=["pdf"],
            help="Upload your complete brand guidelines document",
            key="brand_book_uploader"
        )

        if brand_book_file:
            st.success(f"✅ {brand_book_file.name} uploaded!")

            brand_name_input = st.text_input(
                "Brand Name",
                placeholder="e.g., Acme Corporation",
                help="Enter your brand name",
                key="brand_name_input"
            )

            if st.button("🧠 Analyze Brand Book", type="primary", use_container_width=True, disabled=not brand_name_input, key="analyze_brand_book_btn"):
                with st.spinner("Analyzing brand book with GPT-4 Vision... This may take 2-5 minutes."):
                    try:
                        from app.core.brandbook_analyzer import brandbook_analyzer
                        from uuid import UUID
                        from io import BytesIO

                        # Note: Requires pdf2image and PyPDF2
                        st.info("📄 Extracting pages and analyzing with AI...")

                        # Read PDF
                        brand_book_file.seek(0)
                        pdf_bytes = BytesIO(brand_book_file.read())

                        # Analyze
                        org_id = UUID(st.session_state.org_id)
                        result = brandbook_analyzer.analyze_brand_book_pdf(
                            org_id=org_id,
                            pdf_file=pdf_bytes,
                            brand_name=brand_name_input
                        )

                        st.success("✅ Brand book analysis complete!")
                        st.balloons()

                        # Show results
                        st.markdown("### 📊 Analysis Results")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Pages Analyzed", result.get("pages_analyzed", 0))
                        with col2:
                            st.metric("Total Pages", result.get("total_pages", 0))
                        with col3:
                            confidence = result.get("confidence_score", 0)
                            st.metric("Completeness", f"{confidence:.0%}")

                        guidelines = result.get("guidelines", {})

                        # Show extracted guidelines
                        st.markdown("#### ✨ Extracted Brand Guidelines")

                        with st.expander("🎨 Visual Identity", expanded=True):
                            visual = guidelines.get("visual_identity", {})
                            if visual:
                                st.json(visual)
                            else:
                                st.info("No visual identity guidelines extracted")

                        with st.expander("📸 Imagery Guidelines"):
                            imagery = guidelines.get("imagery_guidelines", {})
                            if imagery:
                                st.json(imagery)
                            else:
                                st.info("No imagery guidelines extracted")

                        with st.expander("💬 Brand Messaging"):
                            messaging = guidelines.get("brand_messaging", {})
                            if messaging:
                                st.json(messaging)
                            else:
                                st.info("No messaging guidelines extracted")

                        with st.expander("📐 Layout & Design"):
                            layout = guidelines.get("layout_system", {})
                            principles = guidelines.get("design_principles", {})
                            if layout or principles:
                                st.json({"layout_system": layout, "design_principles": principles})
                            else:
                                st.info("No layout guidelines extracted")

                        st.success("🎉 Your brand book is now the AI's knowledge base! All new designs will follow these guidelines.")

                    except ImportError as ie:
                        st.error("Missing required packages. Please install:")
                        st.code("pip install pdf2image PyPDF2 Pillow")
                        st.info("Note: pdf2image also requires poppler. On Mac: brew install poppler")
                        logger.error(f"Import error: {str(ie)}")
                    except Exception as e:
                        logger.error(f"Error analyzing brand book: {str(e)}")
                        st.error(f"Error: {str(e)}")
                        import traceback
                        with st.expander("Show error details"):
                            st.code(traceback.format_exc())

            elif not brand_name_input:
                st.warning("⚠️ Please enter your brand name to proceed")
        else:
            st.info("👆 Upload your brand book PDF (up to 20 pages will be analyzed)")

    st.markdown("---")

    # Brand Example Images Section
    st.markdown("## 🎨 Upload Brand Example Images")
    st.info("""
    **📸 Help the AI learn your brand style!**

    Upload 3-5 examples of your past designs (social media posts, ads, banners, etc.).
    The AI will analyze them using GPT-4 Vision to understand your brand's visual DNA:
    - Layout and composition patterns
    - Color usage and palette
    - Typography and text placement
    - Visual style and mood
    - Brand element positioning

    **The more examples you provide, the better the AI understands your brand!**
    """)

    with st.expander("📤 Upload Brand Examples", expanded=False):
        st.markdown("### Upload Your Best Design Examples")

        example_images = st.file_uploader(
            "Select 3-5 past design examples",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload your best past designs so AI can learn your brand style"
        )

        if example_images:
            st.success(f"✅ {len(example_images)} examples uploaded!")

            # Show thumbnails
            cols = st.columns(min(len(example_images), 5))
            for idx, img_file in enumerate(example_images[:5]):
                with cols[idx]:
                    try:
                        # Read bytes and display to avoid BytesIO issues
                        img_file.seek(0)
                        img_bytes = img_file.read()
                        img_file.seek(0)  # Reset for later use
                        st.image(img_bytes, caption=f"Example {idx+1}", use_container_width=True)
                    except Exception as e:
                        st.warning(f"Preview {idx+1} unavailable")

            if len(example_images) > 5:
                st.warning(f"ℹ️ Only the first 5 examples will be analyzed. You uploaded {len(example_images)}.")

            # Analyze button
            if st.button("🧠 Analyze Brand Examples", type="primary", use_container_width=True):
                with st.spinner("Analyzing your brand examples with GPT-4 Vision... This may take 1-2 minutes."):
                    try:
                        from app.core.brand_analyzer import brand_analyzer
                        from app.core.storage import storage
                        from uuid import UUID
                        import time

                        # Upload examples to storage and get URLs
                        example_urls = []
                        for idx, img_file in enumerate(example_images[:5]):
                            # Upload to storage
                            img_file.seek(0)
                            file_path = f"{st.session_state.org_id}/brand_examples/example_{int(time.time())}_{idx}.png"

                            public_url = storage.upload_file(
                                bucket_type="assets",
                                file_path=file_path,
                                file_data=img_file,
                                content_type="image/png"
                            )
                            example_urls.append(public_url)

                        # Analyze examples
                        org_id = UUID(st.session_state.org_id)
                        analysis = brand_analyzer.analyze_brand_examples(
                            org_id=org_id,
                            example_urls=example_urls
                        )

                        # Display results
                        st.success("✅ Brand analysis complete!")

                        st.markdown("### 📊 Analysis Results")

                        confidence = analysis.get("confidence_score", 0)
                        st.metric("Analysis Confidence", f"{confidence:.0%}")

                        synthesis = analysis.get("synthesis", {})

                        if synthesis.get("brand_signature"):
                            st.markdown("#### 🎯 Brand Signature")
                            st.info(synthesis["brand_signature"])

                        if synthesis.get("visual_style_dna"):
                            st.markdown("#### 🎨 Visual Style DNA")
                            keywords = synthesis["visual_style_dna"].get("keywords", [])
                            st.write(", ".join(keywords))

                        if synthesis.get("color_dna"):
                            st.markdown("#### 🌈 Color Patterns")
                            palette = synthesis["color_dna"].get("palette", [])
                            if palette:
                                color_cols = st.columns(len(palette[:5]))
                                for i, color in enumerate(palette[:5]):
                                    with color_cols[i]:
                                        st.markdown(f"""
                                        <div style="background-color: {color}; padding: 20px; border-radius: 8px; text-align: center; color: white; text-shadow: 1px 1px 2px black;">
                                            {color}
                                        </div>
                                        """, unsafe_allow_html=True)

                        guidelines = analysis.get("guidelines", {})

                        if guidelines.get("must_include") or guidelines.get("must_avoid"):
                            st.markdown("#### ✅ Design Guidelines")
                            col1, col2 = st.columns(2)

                            with col1:
                                if guidelines.get("must_include"):
                                    st.markdown("**Must Include:**")
                                    for item in guidelines["must_include"]:
                                        st.write(f"✅ {item}")

                            with col2:
                                if guidelines.get("must_avoid"):
                                    st.markdown("**Must Avoid:**")
                                    for item in guidelines["must_avoid"]:
                                        st.write(f"❌ {item}")

                        st.success("🎉 Your AI agent now understands your brand! New designs will match your style.")

                    except Exception as e:
                        logger.error(f"Error analyzing brand examples: {str(e)}")
                        st.error(f"Error analyzing examples: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.info("👆 Upload 3-5 of your best past designs to help the AI learn your brand style")

    st.markdown("---")

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