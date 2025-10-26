"""
Onboard Brand Kit Page
Upload logos, fonts, and define brand guidelines
"""
import streamlit as st
from io import BytesIO
from app.core.schemas import BrandKitCreate, BrandColors, BrandStyle
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

    # Combined Brand Analysis Section (PRIORITY!)
    st.markdown("## 🧠 AI Brand Analysis")
    st.info("""
    **🎨 Let AI learn your brand identity!**

    Upload your brand materials and AI will analyze them to understand your brand:
    - **Brand Book PDF**: Extract colors, typography, guidelines, brand voice
    - **Example Designs**: Analyze your existing designs to learn your visual style

    You can upload both for best results, or just one!
    """)

    with st.expander("📤 Upload Brand Materials & Analyze", expanded=True):
        # Create two columns for uploads
        col_pdf, col_images = st.columns(2)

        brand_book_file = None
        example_images = None

        with col_pdf:
            st.markdown("### 📖 Brand Book PDF")
            brand_book_file = st.file_uploader(
                "Upload brand guidelines PDF",
                type=["pdf"],
                help="Upload your complete brand guidelines document",
                key="brand_book_uploader"
            )
            if brand_book_file:
                st.success(f"✅ {brand_book_file.name}")

        with col_images:
            st.markdown("### 🎨 Example Designs")
            example_images = st.file_uploader(
                "Upload 3-5 design examples",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                help="Upload past designs to help AI learn your style",
                key="example_images_uploader"
            )
            if example_images:
                st.success(f"✅ {len(example_images)} image(s)")

        # Show thumbnails if images uploaded
        if example_images and len(example_images) > 0:
            st.markdown("#### Preview:")
            cols = st.columns(min(len(example_images), 5))
            for idx, img_file in enumerate(example_images[:5]):
                with cols[idx]:
                    try:
                        img_file.seek(0)
                        img_bytes = img_file.read()
                        img_file.seek(0)
                        st.image(img_bytes, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Preview unavailable")

        st.markdown("---")

        # Brand name input
        brand_name_input = st.text_input(
            "Brand Name",
            placeholder="e.g., Acme Corporation",
            help="Enter your brand name",
            key="brand_name_unified"
        )

        # Brand Kit Selector - Which kit should this analysis update?
        selected_brand_kit_id = None
        if existing_kits and len(existing_kits) > 0:
            st.markdown("#### 🎯 Which brand kit should this update?")

            # Create options for selectbox
            kit_options = {kit.name: kit.id for kit in existing_kits}
            kit_options["➕ Create New Brand Kit"] = None

            selected_kit_name = st.selectbox(
                "Select brand kit to update:",
                options=list(kit_options.keys()),
                help="Choose an existing brand kit to update, or create a new one",
                key="brand_kit_selector"
            )

            selected_brand_kit_id = kit_options[selected_kit_name]

            if selected_brand_kit_id:
                st.success(f"✅ Will update: **{selected_kit_name}**")
            else:
                st.info("💡 A new brand kit will be created")

        # Single analysis button
        can_analyze = (brand_book_file is not None or (example_images and len(example_images) > 0)) and brand_name_input

        # Debug info
        if not can_analyze:
            if not brand_name_input:
                st.info("ℹ️ Please enter brand name above")
            elif not brand_book_file and not (example_images and len(example_images) > 0):
                st.info("ℹ️ Please upload at least one: PDF or images")

        if st.button("🧠 Analyze Brand Materials", type="primary", use_container_width=True, disabled=not can_analyze, key="unified_analyze_btn"):
            st.write(f"🔍 Debug: PDF={brand_book_file is not None}, Images={len(example_images) if example_images else 0}")

            with st.spinner("Analyzing your brand materials with AI... This may take 2-5 minutes."):
                try:
                    from app.core.brandbook_analyzer import brandbook_analyzer
                    from app.core.brand_intelligence import brand_intelligence
                    from app.core.logo_extractor import logo_extractor
                    from app.core.storage import storage
                    from uuid import UUID
                    import time

                    org_id = UUID(st.session_state.org_id)
                    analysis_results = {}
                    pdf_guidelines = None
                    examples_analysis = None
                    logo_info = None

                    st.info(f"Starting analysis... PDF: {brand_book_file is not None}, Images: {len(example_images) if example_images else 0}")

                    # Analyze PDF if provided
                    if brand_book_file:
                        with st.status("📄 Analyzing brand book PDF...", expanded=True) as status:
                            st.write("Reading PDF file...")
                            brand_book_file.seek(0)
                            pdf_bytes = BytesIO(brand_book_file.read())
                            st.write(f"PDF size: {len(pdf_bytes.getvalue())} bytes")

                            try:
                                st.write("Calling brandbook_analyzer...")
                                pdf_result = brandbook_analyzer.analyze_brand_book_pdf(
                                    org_id=org_id,
                                    pdf_file=pdf_bytes,
                                    brand_name=brand_name_input
                                )
                                st.write(f"Analysis complete! Result keys: {list(pdf_result.keys())}")
                                analysis_results['pdf'] = pdf_result
                                pdf_guidelines = pdf_result.get("guidelines", {})

                                # Extract logo from PDF
                                st.write("🔍 Searching for logo in brand book...")
                                try:
                                    # Get pages data from analyzer (we need to extract this)
                                    from app.core.brandbook_analyzer import brandbook_analyzer as ba
                                    pdf_bytes.seek(0)
                                    pages_data = ba._extract_pdf_pages(pdf_bytes)

                                    if pages_data:
                                        logo_result = logo_extractor.extract_logo_from_pdf_pages(
                                            pdf_pages=pages_data,
                                            brand_name=brand_name_input
                                        )

                                        if logo_result:
                                            logo_info = logo_result
                                            st.success(f"✅ Logo found on page {logo_result.get('page_number')}!")
                                            analysis_results['logo'] = logo_result
                                        else:
                                            st.info("ℹ️ No logo detected in brand book (first 5 pages checked)")
                                except Exception as logo_error:
                                    logger.warning(f"Logo extraction failed: {str(logo_error)}")
                                    st.warning("⚠️ Could not extract logo, but analysis continues")

                                status.update(label="✅ Brand book PDF analyzed!", state="complete")
                            except Exception as pdf_error:
                                logger.error(f"PDF analysis failed: {str(pdf_error)}")
                                status.update(label=f"⚠️ PDF analysis failed", state="error")
                                st.error(f"Error: {str(pdf_error)}")
                                import traceback
                                with st.expander("Show PDF error details"):
                                    st.code(traceback.format_exc())

                    # Analyze example images if provided
                    if example_images and len(example_images) > 0:
                        st.info("🎨 Uploading brand example images...")

                        try:
                            # Upload examples to storage (simplified - no AI analysis)
                            example_urls = []
                            for idx, img_file in enumerate(example_images[:5]):
                                img_file.seek(0)
                                file_path = f"{st.session_state.org_id}/brand_examples/example_{int(time.time())}_{idx}.png"

                                public_url = storage.upload_file(
                                    bucket_type="assets",
                                    file_path=file_path,
                                    file_data=img_file,
                                    content_type="image/png"
                                )
                                example_urls.append(public_url)

                            # Store URLs but skip AI analysis (we removed brand_analyzer)
                            examples_analysis = {
                                "example_urls": example_urls,
                                "note": "Example images uploaded but not analyzed"
                            }
                            analysis_results['images'] = examples_analysis
                            st.success(f"✅ Uploaded {len(example_urls)} brand examples!")
                        except Exception as img_error:
                            logger.error(f"Image upload failed: {str(img_error)}")
                            st.warning(f"⚠️ Image upload failed: {str(img_error)}")
                            import traceback
                            with st.expander("Show image error details"):
                                st.code(traceback.format_exc())

                    # Merge and save brand intelligence
                    st.write(f"🔍 Debug: analysis_results has {len(analysis_results)} items: {list(analysis_results.keys())}")

                    if pdf_guidelines or examples_analysis:
                        st.info("💾 Saving brand intelligence to database...")

                        # Merge brand data
                        merged_intelligence = brand_intelligence.merge_brand_data(
                            pdf_guidelines=pdf_guidelines,
                            examples_analysis=examples_analysis,
                            brand_name=brand_name_input
                        )

                        # Save to database
                        try:
                            # Determine brand_kit_id to save to
                            save_brand_kit_id = selected_brand_kit_id
                            if not save_brand_kit_id:
                                # Fall back to first kit if none selected
                                brand_kits_list = brand_kit_manager.get_brand_kits_by_org(org_id)
                                if brand_kits_list:
                                    save_brand_kit_id = brand_kits_list[0].id
                                    st.warning(f"⚠️ No kit selected, saving to: {brand_kits_list[0].name}")

                            brand_intelligence.save_brand_intelligence(
                                org_id=org_id,
                                brand_name=brand_name_input,
                                guidelines=merged_intelligence,
                                examples_analysis=examples_analysis,
                                brand_kit_id=save_brand_kit_id
                            )
                            st.success("✅ Brand intelligence saved! This will be used for all future designs.")

                            # CRITICAL: Also save to brand_brain so Chat can use it
                            try:
                                from app.core.brand_brain import brand_brain, BrandTokens, BrandPolicies

                                # Determine which brand_kit_id to use
                                target_brand_kit_id = selected_brand_kit_id
                                if not target_brand_kit_id:
                                    # Create new brand kit if none selected
                                    st.info("Creating new brand kit...")
                                    # Get brand_kit_id from the first brand kit OR create one
                                    brand_kits = brand_kit_manager.get_brand_kits_by_org(org_id)
                                    if brand_kits:
                                        target_brand_kit_id = brand_kits[0].id
                                        st.warning(f"⚠️ Using first brand kit: {brand_kits[0].name}")
                                    else:
                                        st.error("❌ No brand kits found! Please create one first.")
                                        target_brand_kit_id = None
                                else:
                                    st.success(f"✅ Updating selected brand kit")

                                if not target_brand_kit_id:
                                    st.error("Cannot save - no brand kit ID available")
                                else:
                                    # Convert brand_intelligence to BrandTokens format
                                    visual = merged_intelligence.get("visual_identity", {})
                                    messaging = merged_intelligence.get("brand_messaging", {})
                                    imagery = merged_intelligence.get("imagery_guidelines", {})

                                    # Extract colors from brandbook analyzer format
                                    colors_data = visual.get("colors", {})

                                    # Get hex values from color objects
                                    primary_hex = "#4F46E5"  # default
                                    secondary_hex = "#7C3AED"  # default
                                    accent_hex = "#F59E0B"  # default

                                    # Extract from new brandbook analyzer format
                                    if "primary" in colors_data:
                                        if isinstance(colors_data["primary"], dict):
                                            primary_hex = colors_data["primary"].get("hex", primary_hex)
                                        else:
                                            primary_hex = colors_data["primary"]

                                    if "secondary" in colors_data:
                                        if isinstance(colors_data["secondary"], dict):
                                            secondary_hex = colors_data["secondary"].get("hex", secondary_hex)
                                        else:
                                            secondary_hex = colors_data["secondary"]

                                    if "accent" in colors_data:
                                        accent_data = colors_data["accent"]
                                        if isinstance(accent_data, list) and len(accent_data) > 0:
                                            if isinstance(accent_data[0], dict):
                                                accent_hex = accent_data[0].get("hex", accent_hex)
                                            else:
                                                accent_hex = accent_data[0]
                                        elif isinstance(accent_data, dict):
                                            accent_hex = accent_data.get("hex", accent_hex)
                                        else:
                                            accent_hex = accent_data

                                    logger.info(f"✅ Extracted colors: Primary={primary_hex}, Secondary={secondary_hex}, Accent={accent_hex}")

                                    # Extract tokens
                                    tokens_data = {
                                        "color": {
                                            "primary": primary_hex,
                                            "secondary": secondary_hex,
                                            "accent": accent_hex,
                                            "background": "#FFFFFF",
                                            "text": "#111111",
                                            "min_contrast": 4.5
                                        },
                                        "type": {
                                            "heading": {
                                                "family": visual.get("primary_font", "Inter"),
                                                "weights": [700],
                                                "scale": [48, 36, 28]
                                            },
                                            "body": {
                                                "family": visual.get("body_font", "Inter"),
                                                "weights": [400],
                                                "size": 16
                                            }
                                        },
                                        "logo": {
                                            "variants": [{"name": "full", "path": "", "on": "light"}],
                                            "min_px": 128,
                                            "safe_zone": "1x",
                                            "allowed_positions": ["TL", "TR", "BR"]
                                        },
                                        "layout": {"grid": 12, "spacing": 8, "radius": 16},
                                        "templates": {},
                                        "cta_whitelist": messaging.get("cta_whitelist", ["Learn More", "Get Started", "Try Free"])
                                    }

                                    # Extract policies
                                    policies_data = {
                                        "voice": messaging.get("voice_attributes", ["Professional", "Trustworthy", "Innovative"]),
                                        "forbid": messaging.get("forbidden_terms", [])
                                    }

                                    tokens = BrandTokens.from_dict(tokens_data)
                                    policies = BrandPolicies.from_dict(policies_data)

                                    # Save to the selected/determined brand kit
                                    brand_brain.save_brand_brain(target_brand_kit_id, tokens, policies)
                                    st.success(f"✅ Brand Brain updated! Chat will now use your brand book guidelines.")

                                    # Show what colors were extracted
                                    st.info(f"🎨 Extracted Colors: Primary={primary_hex}, Secondary={secondary_hex}, Accent={accent_hex}")

                            except Exception as brain_error:
                                logger.warning(f"Could not update brand_brain: {brain_error}")
                                st.warning(f"⚠️ Brand intelligence saved but Chat integration needs manual setup")
                                import traceback
                                st.error(traceback.format_exc())

                        except Exception as save_error:
                            logger.error(f"Failed to save brand intelligence: {str(save_error)}")
                            st.warning(f"⚠️ Could not save to database: {str(save_error)}")

                    # Show combined results
                    if analysis_results:
                        st.success("✅ Brand analysis complete!")
                        st.balloons()

                        st.markdown("### 📊 Analysis Results")

                        # Debug: Show what we got
                        st.write(f"Results contain: {', '.join(analysis_results.keys())}")

                        # Show PDF results if available
                        if 'pdf' in analysis_results:
                            pdf_result = analysis_results['pdf']
                            st.markdown("#### 📖 Brand Book Analysis")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Pages Analyzed", pdf_result.get("pages_analyzed", 0))
                            with col2:
                                st.metric("Total Pages", pdf_result.get("total_pages", 0))
                            with col3:
                                confidence = pdf_result.get("confidence_score", 0)
                                st.metric("Completeness", f"{confidence:.0%}")

                            guidelines = pdf_result.get("guidelines", {})

                            with st.expander("🎨 Visual Identity"):
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

                        # Show image analysis results if available
                        if 'images' in analysis_results:
                            images_result = analysis_results['images']
                            st.markdown("#### 🎨 Design Examples Analysis")

                            confidence = images_result.get("confidence_score", 0)
                            st.metric("Analysis Confidence", f"{confidence:.0%}")

                            synthesis = images_result.get("synthesis", {})

                            if synthesis.get("brand_signature"):
                                st.markdown("**🎯 Brand Signature**")
                                st.info(synthesis["brand_signature"])

                            if synthesis.get("visual_style_dna"):
                                st.markdown("**🎨 Visual Style DNA**")
                                keywords = synthesis["visual_style_dna"].get("keywords", [])
                                st.write(", ".join(keywords))

                            if synthesis.get("color_dna"):
                                st.markdown("**🌈 Color Patterns**")
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

                        st.success("🎉 Your AI agent now understands your brand! New designs will match your style.")

                    else:
                        st.error("❌ No analysis could be completed. Please check the error details above.")

                except Exception as e:
                    logger.error(f"Error in unified analysis: {str(e)}")
                    st.error(f"Error: {str(e)}")
                    import traceback
                    with st.expander("Show error details"):
                        st.code(traceback.format_exc())

        elif not brand_name_input:
            st.warning("⚠️ Please enter your brand name to proceed")
        elif not brand_book_file and not (example_images and len(example_images) > 0):
            st.info("👆 Upload at least one: Brand book PDF or design examples")

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

                    # Create brand kit
                    brand_kit = brand_kit_manager.create_brand_kit(
                        org_id=org_id,
                        brand_kit_data=brand_kit_data
                    )

                    # Upload assets if provided
                    from app.core.storage import storage
                    from app.core.schemas import BrandAssetCreate, AssetType
                    import time

                    assets = []

                    # Upload logo if provided
                    if logo_file:
                        logo_file.seek(0)
                        file_path = f"{org_id}/brand_assets/logo_{int(time.time())}.png"
                        logo_url = storage.upload_file(
                            bucket_type="assets",
                            file_path=file_path,
                            file_data=logo_file,
                            content_type="image/png"
                        )

                        # Add logo asset
                        logo_asset = brand_kit_manager.add_brand_asset(
                            asset_data=BrandAssetCreate(
                                brand_kit_id=brand_kit.id,
                                type=AssetType.LOGO,
                                url=logo_url,
                                meta={"filename": logo_file.name}
                            )
                        )
                        assets.append(logo_asset)

                    # Upload font if provided
                    if font_file:
                        font_file.seek(0)
                        file_path = f"{org_id}/brand_assets/font_{int(time.time())}.ttf"
                        font_url = storage.upload_file(
                            bucket_type="assets",
                            file_path=file_path,
                            file_data=font_file,
                            content_type="font/ttf"
                        )

                        # Add font asset
                        font_asset = brand_kit_manager.add_brand_asset(
                            asset_data=BrandAssetCreate(
                                brand_kit_id=brand_kit.id,
                                type=AssetType.FONT,
                                url=font_url,
                                meta={"filename": font_file.name}
                            )
                        )
                        assets.append(font_asset)

                    st.success("✅ Brand kit created successfully!")

                    # Show summary
                    st.balloons()

                    st.markdown("### ✨ Brand Kit Summary")
                    st.write(f"**Name**: {brand_kit.name}")
                    st.write(f"**Colors**: {brand_kit.colors.primary}, {brand_kit.colors.secondary}")
                    st.write(f"**Style**: {', '.join(brand_kit.style.descriptors)}")
                    st.write(f"**Assets**: {len(assets)} uploaded")

                    st.success("✅ Next: Go to Chat Create page to generate designs with this brand kit!")

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
