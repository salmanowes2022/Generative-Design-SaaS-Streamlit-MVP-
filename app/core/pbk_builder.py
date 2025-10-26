"""
Promptable Brand Kit (PBK) Builder
====================================
Converts extracted brand guidelines into an LLM-optimized format
for intelligent, brand-consistent design generation.

This enables the AI to act as a professional brand designer with
complete knowledge of the brand's visual language, rules, and personality.
"""

from typing import Dict, List, Any, Optional
import json
from app.infra.logging import get_logger

logger = get_logger(__name__)


class PromptableBrandKit:
    """
    Transforms comprehensive brand guidelines into a structured,
    LLM-friendly format (Promptable Brand Kit).

    This allows the AI to:
    - Understand the complete brand identity
    - Choose appropriate design archetypes
    - Apply spacing, typography, and color systems correctly
    - Embed brand assets (characters, icons, patterns)
    - Follow DO/DON'T rules
    - Match the brand's mood and personality
    """

    def __init__(self, brand_guidelines: Dict[str, Any]):
        """
        Initialize with extracted brand guidelines.

        Args:
            brand_guidelines: Complete brand guidelines from brandbook_analyzer
        """
        self.guidelines = brand_guidelines or {}
        logger.info("Initializing Promptable Brand Kit builder")

    def build_pbk(self) -> Dict[str, Any]:
        """
        Build complete Promptable Brand Kit.

        Returns:
            Structured JSON optimized for LLM consumption
        """
        logger.info("Building Promptable Brand Kit from guidelines")

        pbk = {
            "brand_name": self.guidelines.get("brand_name", "Brand"),
            "brand_identity": self._build_identity(),
            "design_archetypes": self._build_archetypes(),
            "brand_assets": self._build_assets(),
            "visual_rules": self._build_rules(),
            "mood_and_personality": self._build_mood()
        }

        logger.info(f"✅ PBK built with {len(pbk['design_archetypes'])} archetypes")
        return pbk

    def _build_identity(self) -> Dict[str, Any]:
        """Extract and structure core brand identity elements."""
        visual = self.guidelines.get("visual_identity", {})
        colors_data = visual.get("colors", {})
        typography = visual.get("typography", {})
        spacing = visual.get("spacing", {})
        borders = visual.get("borders_shadows", {})

        identity = {
            "colors": self._extract_color_palette(colors_data),
            "typography": self._extract_typography(typography),
            "spacing": self._extract_spacing(spacing),
            "visual_elements": self._extract_visual_elements(borders)
        }

        return identity

    def _extract_color_palette(self, colors_data: Dict) -> Dict[str, Any]:
        """Extract and structure color palette with usage guidance."""
        palette = {
            "primary": self._extract_color_detail(colors_data.get("primary", {})),
            "secondary": self._extract_color_detail(colors_data.get("secondary", {})),
            "accent": self._extract_color_list(colors_data.get("accent", [])),
            "neutral": self._extract_neutral_colors(colors_data.get("neutral", [])),
            "semantic": colors_data.get("semantic", {}),
            "gradients": colors_data.get("gradients", []),
            "usage_rules": colors_data.get("usage_rules", [
                "Use primary for main CTAs and interactive elements",
                "Use secondary for backgrounds and supporting elements",
                "Use accent colors sparingly for highlights"
            ])
        }

        return palette

    def _extract_color_detail(self, color_obj: Any) -> Dict[str, str]:
        """Extract color with hex, name, and usage."""
        if isinstance(color_obj, dict):
            return {
                "hex": color_obj.get("hex", "#000000"),
                "name": color_obj.get("name", ""),
                "usage": color_obj.get("usage", "")
            }
        elif isinstance(color_obj, str):
            return {"hex": color_obj, "name": "", "usage": ""}
        else:
            return {"hex": "#000000", "name": "", "usage": ""}

    def _extract_color_list(self, accent_data: Any) -> List[Dict]:
        """Handle accent colors which might be array or single value."""
        if isinstance(accent_data, list):
            return [self._extract_color_detail(c) for c in accent_data]
        else:
            return [self._extract_color_detail(accent_data)]

    def _extract_neutral_colors(self, neutral_data: Any) -> Dict[str, str]:
        """Extract neutral color scale."""
        if isinstance(neutral_data, list):
            neutrals = {}
            for item in neutral_data:
                if isinstance(item, dict):
                    name = item.get("name", "gray")
                    neutrals[name] = item.get("hex", "#808080")
            return neutrals
        return {"gray": "#808080", "light": "#F5F5F5", "dark": "#1F1F1F"}

    def _extract_typography(self, typography: Dict) -> Dict[str, Any]:
        """Extract typography system."""
        return {
            "heading": {
                "family": typography.get("heading_font", {}).get("family", "Inter"),
                "weights": typography.get("heading_font", {}).get("weights", [700, 900]),
                "sizes": typography.get("heading_font", {}).get("sizes", {"h1": "48px", "h2": "36px", "h3": "24px"}),
                "line_height": typography.get("heading_font", {}).get("line_height", "1.2")
            },
            "body": {
                "family": typography.get("body_font", {}).get("family", "Inter"),
                "weights": typography.get("body_font", {}).get("weights", [400, 500]),
                "sizes": typography.get("body_font", {}).get("sizes", {"body": "16px", "small": "14px"}),
                "line_height": typography.get("body_font", {}).get("line_height", "1.5")
            },
            "hierarchy": typography.get("hierarchy", []),
            "usage_rules": typography.get("usage_rules", [])
        }

    def _extract_spacing(self, spacing: Dict) -> Dict[str, Any]:
        """Extract spacing system."""
        return {
            "base_unit": spacing.get("base_unit", "8px"),
            "scale": spacing.get("scale", [8, 16, 24, 32, 48, 64, 96]),
            "margins": spacing.get("margins", "Use scale values for consistent spacing"),
            "padding": spacing.get("padding", "Use scale values for consistent padding"),
            "gaps": spacing.get("gaps", "Use scale values for gaps between elements")
        }

    def _extract_visual_elements(self, borders: Dict) -> Dict[str, Any]:
        """Extract borders, shadows, and visual elements."""
        return {
            "border_radius": borders.get("border_radius", ["8px", "16px"]),
            "shadows": borders.get("shadows", []),
            "border_width": borders.get("border_width", "1px")
        }

    def _build_archetypes(self) -> List[Dict[str, Any]]:
        """
        Build design archetypes based on brand personality.

        Archetypes are reusable design patterns that match
        different content types and brand moods.
        """
        patterns = self.guidelines.get("design_patterns", {})
        visual_style = self.guidelines.get("visual_style", {})
        layout = self.guidelines.get("layout_system", {})

        aesthetic = visual_style.get("overall_aesthetic", "").lower()
        mood = visual_style.get("mood", "").lower()

        archetypes = []

        # Always include versatile archetypes
        archetypes.append(self._create_hero_archetype(patterns, aesthetic))
        archetypes.append(self._create_card_archetype(patterns, aesthetic))
        archetypes.append(self._create_split_archetype(patterns, aesthetic))

        # Add mood-specific archetypes
        if "bold" in aesthetic or "energetic" in mood:
            archetypes.append(self._create_bold_gradient_archetype(patterns))

        if "minimal" in aesthetic or "clean" in aesthetic:
            archetypes.append(self._create_minimal_archetype(patterns))

        if "luxurious" in mood or "premium" in mood:
            archetypes.append(self._create_premium_archetype(patterns))

        logger.info(f"Created {len(archetypes)} design archetypes")
        return archetypes

    def _create_hero_archetype(self, patterns: Dict, aesthetic: str) -> Dict:
        """Create versatile hero section archetype."""
        return {
            "name": "Hero Section",
            "description": "Full-width hero section with large headline, subheader, and prominent CTA. Perfect for main messages and product launches.",
            "layout_structure": "Centered content, single column, full-width background, logo in top corner",
            "when_to_use": ["Product launches", "Main announcements", "Campaign landing sections", "Premium features"],
            "composition": {
                "text_hierarchy": "Large headline (h1), medium subheader, prominent CTA button",
                "visual_weight": "Text-focused with background visual treatment",
                "cta_placement": "Below text, centered",
                "logo_placement": "Top left with safe spacing"
            },
            "color_strategy": "Use gradient or solid primary color for background, white text, accent color for CTA",
            "spacing_approach": "Generous spacing (48px+ between elements) for impact",
            "best_for_mood": ["Bold", "Confident", "Premium", "Innovative"]
        }

    def _create_card_archetype(self, patterns: Dict, aesthetic: str) -> Dict:
        """Create card-based archetype."""
        card_styles = patterns.get("card_styles", [{}])
        card = card_styles[0] if card_styles else {}

        return {
            "name": "Information Card",
            "description": "Contained card design with subtle elevation, clean layout. Great for features, updates, or secondary content.",
            "layout_structure": "Boxed card, centered or aligned content, subtle shadow, rounded corners",
            "when_to_use": ["Feature highlights", "Updates", "Notifications", "List items", "Secondary CTAs"],
            "composition": {
                "text_hierarchy": "Medium headline, body text, optional CTA",
                "visual_weight": "Balanced text and whitespace",
                "cta_placement": "Bottom or right side",
                "logo_placement": "Top left within card or omitted"
            },
            "color_strategy": "Neutral background (white or light gray), colored accents for CTAs and highlights",
            "spacing_approach": "Medium spacing (24-32px) for readability without waste",
            "best_for_mood": ["Professional", "Clean", "Approachable", "Informative"]
        }

    def _create_split_archetype(self, patterns: Dict, aesthetic: str) -> Dict:
        """Create split-screen archetype."""
        return {
            "name": "Split Layout",
            "description": "Two-column design dividing visual and text content. Perfect for product showcases and feature explanations.",
            "layout_structure": "50-50 or 60-40 split, image/graphic on one side, text on other",
            "when_to_use": ["Product features", "Before/after", "Comparisons", "Image + description"],
            "composition": {
                "text_hierarchy": "Headline, body text, CTA in text column",
                "visual_weight": "Balanced between image and text sections",
                "cta_placement": "Within text column, middle or bottom",
                "logo_placement": "Top of text column or centered top"
            },
            "color_strategy": "Different background colors for each side to create clear division",
            "spacing_approach": "Medium to generous (32-48px) to separate sections clearly",
            "best_for_mood": ["Balanced", "Professional", "Feature-focused"]
        }

    def _create_bold_gradient_archetype(self, patterns: Dict) -> Dict:
        """Create bold gradient archetype for energetic brands."""
        return {
            "name": "Bold Gradient",
            "description": "Eye-catching gradient background with large text. Maximum visual impact for announcements.",
            "layout_structure": "Full-bleed gradient, centered white text, rounded CTA",
            "when_to_use": ["Major launches", "Exclusive offers", "Premium upgrades", "Campaign headers"],
            "composition": {
                "text_hierarchy": "Extra large headline, short punchy subheader, bright CTA",
                "visual_weight": "Text as hero, gradient as dramatic backdrop",
                "cta_placement": "Centered below text",
                "logo_placement": "Top left in white or contrasting color"
            },
            "color_strategy": "Vibrant gradient (primary → accent), white text, contrasting CTA button",
            "spacing_approach": "Extra generous (64px+) for dramatic impact",
            "best_for_mood": ["Bold", "Energetic", "Youthful", "Exciting"]
        }

    def _create_minimal_archetype(self, patterns: Dict) -> Dict:
        """Create minimal archetype for clean brands."""
        return {
            "name": "Minimal Composition",
            "description": "Ultra-clean design with maximum whitespace. Sophisticated and focused.",
            "layout_structure": "Asymmetric or centered, generous whitespace, subtle elements",
            "when_to_use": ["Luxury products", "High-end services", "Sophisticated announcements"],
            "composition": {
                "text_hierarchy": "Medium headline, minimal body text, understated CTA",
                "visual_weight": "Mostly negative space, sparse elements",
                "cta_placement": "Bottom left or right, subtle",
                "logo_placement": "Small, top corner or omitted"
            },
            "color_strategy": "Monochrome or very limited palette, subtle accents",
            "spacing_approach": "Maximum whitespace (96px+) for breathing room",
            "best_for_mood": ["Minimal", "Luxurious", "Sophisticated", "Calm"]
        }

    def _create_premium_archetype(self, patterns: Dict) -> Dict:
        """Create premium archetype for luxury brands."""
        return {
            "name": "Premium Experience",
            "description": "Elegant design with refined details, subtle animations, premium feel.",
            "layout_structure": "Balanced asymmetry, refined typography, elegant spacing",
            "when_to_use": ["Premium features", "Exclusive offerings", "VIP content"],
            "composition": {
                "text_hierarchy": "Elegant headline, refined subheader, sophisticated CTA",
                "visual_weight": "Balanced with attention to details",
                "cta_placement": "Strategic placement for flow",
                "logo_placement": "Refined position with proper spacing"
            },
            "color_strategy": "Sophisticated palette with metallic or deep tones",
            "spacing_approach": "Refined spacing that feels luxurious",
            "best_for_mood": ["Luxurious", "Premium", "Exclusive", "Elegant"]
        }

    def _build_assets(self) -> Dict[str, Any]:
        """Structure brand assets for easy embedding."""
        assets = self.guidelines.get("brand_assets", {})

        return {
            "characters": assets.get("characters", []),
            "icons": assets.get("icons", []),
            "patterns": assets.get("patterns_textures", []),
            "illustrations": assets.get("illustrations", []),
            "photography": assets.get("photography_examples", []),
            "graphic_elements": assets.get("graphic_elements", []),
            "usage_guidance": "Use brand assets when they enhance the message. Characters for personality, icons for clarity, patterns for visual interest."
        }

    def _build_rules(self) -> Dict[str, Any]:
        """Extract DO/DON'T rules and layout preferences."""
        usage = self.guidelines.get("usage_guidelines", {})
        layout = self.guidelines.get("layout_system", {})
        design_principles = self.guidelines.get("design_principles", {})

        return {
            "dos": usage.get("dos", []),
            "donts": usage.get("donts", []),
            "layout_preferences": {
                "grid_system": layout.get("grid", "12-column grid"),
                "composition_principles": layout.get("composition_principles", []),
                "whitespace_philosophy": layout.get("whitespace_usage", "Use generous whitespace")
            },
            "design_principles": design_principles.get("key_principles", [])
        }

    def _build_mood(self) -> Dict[str, Any]:
        """Extract brand mood and personality."""
        visual_style = self.guidelines.get("visual_style", {})
        messaging = self.guidelines.get("brand_messaging", {})

        return {
            "overall_aesthetic": visual_style.get("overall_aesthetic", "Modern and professional"),
            "mood": visual_style.get("mood", "Professional and approachable"),
            "personality_traits": messaging.get("personality", []),
            "brand_voice": messaging.get("voice", "Professional"),
            "tone": messaging.get("tone", "Friendly yet professional"),
            "values": messaging.get("values", [])
        }

    def to_json_string(self, indent: int = 2) -> str:
        """Convert PBK to formatted JSON string."""
        pbk = self.build_pbk()
        return json.dumps(pbk, indent=indent)

    def to_system_prompt(self, user_request: str, logo_url: Optional[str] = None) -> str:
        """
        Build complete system prompt with PBK for LLM design generation.

        Args:
            user_request: User's design request (headline, subheader, CTA)
            logo_url: Optional URL to brand logo

        Returns:
            Complete prompt for GPT-4 with full brand context
        """
        pbk_json = self.to_json_string()

        prompt = f"""You are an expert brand designer creating professional HTML/CSS marketing visuals.

Your task is to create a design that is:
1. **Brand-perfect** - Follows ALL brand guidelines exactly
2. **Professional** - Looks like it was made by a skilled designer
3. **Purposeful** - Matches the content type and user's goal
4. **Accessible** - High contrast, readable, WCAG AA compliant

BRAND KIT (USE THIS EXACTLY):
```json
{pbk_json}
```

USER REQUEST:
{user_request}

{"LOGO URL: " + logo_url if logo_url else "NO LOGO PROVIDED - Design without logo"}

DESIGN REQUIREMENTS:

1. **Choose the Right Archetype**
   - Review the design_archetypes in the brand kit
   - Select the archetype that best matches the user's request and brand mood
   - Follow that archetype's layout structure, spacing, and color strategy

2. **Apply Brand Identity Exactly**
   - **CRITICAL**: Use ONLY colors from the brand palette - DO NOT invent or mix colors not in the palette
   - **CRITICAL**: For gradients, only use brand primary and secondary colors - NO purple, NO random colors
   - **CRITICAL**: Use the EXACT font family names from typography.heading.family and typography.body.family
   - Follow the spacing scale (use values from spacing.scale)
   - Apply border radius values from visual_elements

3. **Create Professional Layout**
   - Follow the chosen archetype's composition rules
   - Apply generous spacing for visual breathing room
   - Create clear visual hierarchy (headline > subheader > CTA)
   - Ensure proper contrast (text must be readable)
   - **CRITICAL: For gradient/colored backgrounds, place text DIRECTLY on the background - NO white boxes around text**
   - **CRITICAL: All text must fit completely within the frame - no truncation or cutoff**
   - **CRITICAL: Use proper line-height and text wrapping to ensure full sentences display**

4. **Style Elements Correctly**
   - Button: Use brand's button style or create one following patterns
   - Typography: Follow the hierarchy (heading font for titles, body font for text)
   - **Use brand's EXACT font family names** - Load from Google Fonts if needed
   - Spacing: Use base_unit multiples (8px, 16px, 24px, 32px, 48px, 64px)
   - Shadows: Use brand's shadow values if specified
   - **Text on gradient backgrounds should be WHITE or high-contrast color with NO background boxes**

5. **Embed Logo (if provided)**
   - Place logo according to archetype's logo_placement
   - Ensure proper safe space around logo
   - Make sure logo is visible against background

6. **Make it Responsive**
   - Design should work in 1200px width frame
   - Use modern CSS (flexbox, grid where appropriate)
   - All text must be readable
   - Buttons must be clickable (min 44px height)

7. **Follow Brand Rules**
   - DO: Follow all items in visual_rules.dos
   - DON'T: Avoid all items in visual_rules.donts
   - Respect the brand's mood and personality

OUTPUT FORMAT:
Return ONLY the HTML with inline CSS. No markdown, no explanations.

Structure your HTML like:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- CRITICAL: Load brand fonts FIRST -->
    <!-- For custom fonts like Circular, use CDN or fallback to system fonts -->
    <!-- Example for Circular (Spotify): -->
    <!-- <link href="https://fonts.cdnfonts.com/css/circular-std" rel="stylesheet"> -->
    <!-- If font not available via CDN, use best system fallback -->

    <style>
        /* Your CSS here - use brand colors, fonts, spacing */

        /* IMPORTANT: Define font-face if using custom fonts */
        @font-face {{
            font-family: 'BrandFont';
            src: local('[exact brand font name]'), local('Arial Black');
            font-weight: 700;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: [brand body font], Arial, sans-serif;  /* Always include fallbacks */
            background: [brand background color];
        }}
        .container {{
            width: 1200px;
            height: 630px;
            /* Your design styles */
        }}
        /* More styles... */
    </style>
</head>
<body>
    <div class="container">
        <!-- Your design HTML -->
    </div>
</body>
</html>
```

**FONT LOADING INSTRUCTIONS:**
- For brand fonts like "Circular" (Spotify), "Gotham", "Proxima Nova", etc:
  1. First try: Use actual font name with good fallbacks: `font-family: 'Circular', 'Helvetica Neue', Arial, sans-serif;`
  2. For headings: Use bold system fallback if custom not available: `font-family: 'Circular Bold', 'Arial Black', 'Helvetica Bold', sans-serif;`
  3. The fallbacks ensure readability even if custom font doesn't load
  4. **DO NOT** use generic "sans-serif" alone - always specify good fallback fonts

CRITICAL DESIGN RULES (MUST FOLLOW - THESE ARE MANDATORY):

❌ **ABSOLUTELY FORBIDDEN - DO NOT DO THESE:**
1. **NO WHITE BOXES ON TEXT** - Headlines and subheaders on gradient backgrounds MUST NOT have background-color, background, or any box styling. Text must be styled with color property only.
2. **NO TEXT TRUNCATION** - Every sentence MUST be complete. If text doesn't fit, make it shorter or adjust font size. Never cut off mid-sentence.
3. **NO PLACEHOLDER EMOJIS** - Do not use emojis. They often render as broken boxes. Use text only.
4. **NO GENERIC FONTS** - Must use the exact brand font families specified.

✅ **MANDATORY REQUIREMENTS:**
1. **Text Directly On Background** - Use `color: #FFFFFF` for text on dark gradients. NO background-color, NO background, NO backdrop, NO boxes around text elements.
2. **Complete Sentences** - All text must fit. Adjust font-size if needed to fit complete messages within 1200x630px.
3. **Proper Font Loading** - Use @import for Google Fonts or CDN fonts. Include fallbacks.
4. **High Contrast** - White text on dark backgrounds, or dark text on light backgrounds only.
5. **Clean Hierarchy** - Headline (largest), Subheader (medium), CTA (button with background OK).

SPECIFIC CSS REQUIREMENTS FOR TEXT ON GRADIENTS:
```css
/* ✅ CORRECT - Text directly on gradient */
.headline {{
    color: #FFFFFF;
    font-size: 64px;
    /* NO background property at all */
}}

.subheader {{
    color: #FFFFFF;
    font-size: 24px;
    /* NO background property at all */
}}

/* ❌ WRONG - Do NOT do this */
.headline {{
    background: white;  /* FORBIDDEN */
    background-color: white;  /* FORBIDDEN */
    padding: 20px;  /* Creates box effect */
}}
```

PERFECT EXAMPLE - COPY THIS STRUCTURE EXACTLY:
```css
.container {{
    width: 1200px;
    height: 630px;
    background: linear-gradient(135deg, #1ED760, #0F7A38);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 64px;
    position: relative;
}}

/* ✅ PERFECT - Text with NO boxes */
.headline {{
    color: #FFFFFF;
    font-family: 'Circular Bold', 'Arial Black', sans-serif;
    font-size: 72px;
    font-weight: 900;
    margin: 0 0 24px 0;
    text-align: center;
    line-height: 1.2;
    max-width: 900px;
    /* NOTICE: No background, no background-color, no padding creating boxes */
}}

/* ✅ PERFECT - Subheader with NO boxes */
.subheader {{
    color: #FFFFFF;
    font-family: 'Circular', Arial, sans-serif;
    font-size: 28px;
    font-weight: 400;
    margin: 0 0 48px 0;
    text-align: center;
    line-height: 1.5;
    max-width: 800px;
    /* NOTICE: No background, no background-color, no padding creating boxes */
}}

/* ✅ Button CAN have background */
.cta-button {{
    background: rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
    font-size: 20px;
    font-weight: 600;
    padding: 16px 48px;
    border-radius: 32px;
    border: 2px solid #FFFFFF;
    cursor: pointer;
}}

.logo {{
    position: absolute;
    top: 32px;
    right: 32px;
    width: 60px;
    height: 60px;
}}
```

FINAL CHECKLIST BEFORE GENERATING:
☐ Headlines have NO background property
☐ Subheaders have NO background property
☐ All text is complete sentences (no truncation)
☐ No emojis used
☐ Brand fonts loaded via @import
☐ Text uses only color property on gradients
☐ Only buttons/CTAs have backgrounds

Remember:
- Text directly on gradient = color property ONLY
- NO background, NO background-color on text elements
- Complete sentences that fit
- Professional and polished
- **If you add ANY background to headline or subheader text, you have FAILED**

Now create the design following these rules EXACTLY:"""

        return prompt


# Convenience function for easy import
def build_pbk_from_guidelines(guidelines: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to build PBK from guidelines.

    Args:
        guidelines: Brand guidelines dict from brandbook_analyzer

    Returns:
        Promptable Brand Kit dict
    """
    builder = PromptableBrandKit(guidelines)
    return builder.build_pbk()
