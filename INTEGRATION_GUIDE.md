# AI Design Assistant - Integration Guide

## 🎯 Overview

This guide shows you how to integrate the new AI design assistant features into your existing SaaS platform.

## 📦 New Modules Created

### 1. **BrandBookParser** (`app/core/brandbook_parser.py`)
**Purpose**: Extract brand tokens from uploaded brand books

```python
from app.core.brandbook_parser import BrandBookParser

# Parse brand book
parser = BrandBookParser()
result = parser.parse_file("path/to/brandbook.pdf")

# result contains:
# {
#   "tokens": {...},  # BrandTokens compatible dict
#   "policies": {...}  # BrandPolicies compatible dict
# }

# Save to database
brand_brain.save_brand_brain(
    brand_kit_id=kit.id,
    tokens=BrandTokens.from_dict(result["tokens"]),
    policies=BrandPolicies.from_dict(result["policies"])
)
```

**Supported Formats**: PDF, DOCX, TXT

### 2. **ChatAgentPlanner** (`app/core/chat_agent_planner.py`)
**Purpose**: Conversational AI for design generation

```python
from app.core.chat_agent_planner import ChatAgentPlanner

# Initialize with brand context
agent = ChatAgentPlanner(tokens, policies)

# Chat loop
user_message = "Create a Black Friday Instagram post"
response = agent.chat(user_message)

# Extract design plan
plan = agent.extract_design_plan(response)
# plan = DesignPlan(headline, subhead, cta_text, ...)

# Iterate on design
feedback = "Make it more professional"
updated_plan = agent.iterate_design(plan, feedback)
```

**Features**:
- Multi-turn conversations
- Brand voice enforcement
- Forbidden term detection
- CTA whitelist validation
- Conversation export

### 3. **GridRenderer** (`app/core/renderer_grid.py`)
**Purpose**: Template-free design rendering with grid system

```python
from app.core.renderer_grid import GridRenderer

# Initialize
renderer = GridRenderer(tokens)

# Render design
design_image = renderer.render_design(
    plan=plan,
    background_url="https://...",
    logo_url="https://...",  # Optional
    product_image_url=None
)

# Save to storage
url = renderer.save_design(design_image, org_id="...", filename="design.png")
```

**Features**:
- 12-column responsive grid
- Brand font/color application
- Logo safe zones
- Text wrapping
- Image compositing
- PNG export

### 4. **DesignQualityScorer** (`app/core/quality_scorer.py`)
**Purpose**: Evaluate design quality

```python
from app.core.quality_scorer import DesignQualityScorer

# Score design
scorer = DesignQualityScorer(tokens, quality_threshold=70.0)
score = scorer.score_design(design_image, plan)

# Check results
if score.passed:
    print(f"✅ Quality: {score.overall_score}/100")
else:
    print(f"⚠️ Issues: {score.issues}")
    print(f"💡 Suggestions: {score.suggestions}")

# Auto-improve
improved_design = scorer.auto_improve_design(design_image, plan, score)
```

**Evaluation Dimensions**:
- Text contrast (30%)
- CTA prominence (25%)
- Layout balance (20%)
- Brand accuracy (15%)
- Visual hierarchy (10%)

### 5. **TemplateValidator** (`app/core/template_validator.py`)
**Purpose**: Validate Canva templates

```python
from app.core.template_validator import CanvaTemplateValidator

# Initialize with access token
validator = CanvaTemplateValidator(access_token)

# Inspect template
result = validator.inspect_template("EAG2aiNOtSM")

if result.is_valid:
    print(f"✅ Template has fields: {result.placeholder_fields}")
else:
    print(f"❌ Issues: {result.issues}")
    suggestions = validator.suggest_fixes(result)
```

### 6. **Chat UI** (`app/pages/3_Chat_Create.py`)
**Purpose**: Streamlit chat interface

Ready-to-use conversational UI with:
- Chat message display
- Design plan preview
- Live design generation
- Quality scoring
- Download/export

## 🔄 Integration Workflows

### Workflow 1: Brand Book Upload → Auto-Configure

```python
# In your onboarding flow
def upload_brand_book(file, brand_kit_id):
    """User uploads PDF, auto-extract tokens"""

    # 1. Save uploaded file
    file_path = save_uploaded_file(file)

    # 2. Parse with AI
    parser = BrandBookParser()
    result = parser.parse_file(file_path)

    # 3. Save to brand brain
    tokens = BrandTokens.from_dict(result["tokens"])
    policies = BrandPolicies.from_dict(result["policies"])

    brand_brain.save_brand_brain(
        brand_kit_id=brand_kit_id,
        tokens=tokens,
        policies=policies
    )

    return tokens, policies
```

### Workflow 2: Chat-Based Design Generation

```python
# In your design generation page
def chat_create_design(user_prompt, brand_kit_id):
    """Create design through conversation"""

    # 1. Load brand context
    tokens, policies = brand_brain.get_brand_brain(brand_kit_id)

    # 2. Initialize chat agent
    agent = ChatAgentPlanner(tokens, policies)

    # 3. Process user request
    response = agent.chat(user_prompt)
    plan = agent.extract_design_plan(response)

    if not plan:
        return {"error": "Could not generate design plan", "response": response}

    # 4. Generate background
    generator = OpenAIGenerator(org_id=org_id)
    bg_result = generator.generate_image(
        prompt=plan.background_style,
        aspect_ratio=plan.aspect_ratio
    )

    # 5. Render design (template-free)
    renderer = GridRenderer(tokens)
    design_image = renderer.render_design(
        plan=plan,
        background_url=bg_result["image_url"]
    )

    # 6. Quality check
    scorer = DesignQualityScorer(tokens)
    quality = scorer.score_design(design_image, plan)

    if not quality.passed:
        # Auto-improve
        design_image = scorer.auto_improve_design(design_image, plan, quality)

    # 7. Save and return
    url = renderer.save_design(design_image, org_id, "design.png")

    return {
        "success": True,
        "design_url": url,
        "quality_score": quality.overall_score,
        "plan": plan.to_dict()
    }
```

### Workflow 3: Template Validation Before Use

```python
# Before using a Canva template
def validate_canva_template(template_id, access_token):
    """Check if template is properly configured"""

    validator = CanvaTemplateValidator(access_token)
    result = validator.inspect_template(template_id)

    if not result.is_valid:
        # Show user what's wrong
        return {
            "valid": False,
            "issues": result.issues,
            "suggestions": validator.suggest_fixes(result)
        }

    return {"valid": True, "fields": result.placeholder_fields}
```

### Workflow 4: Quality-Gated Design Generation

```python
# Ensure high-quality output
def generate_with_quality_gate(plan, tokens, max_retries=3):
    """Generate design with automatic quality retries"""

    for attempt in range(max_retries):
        # Generate
        design_image = generate_design(plan, tokens)

        # Score
        scorer = DesignQualityScorer(tokens, quality_threshold=75.0)
        quality = scorer.score_design(design_image, plan)

        if quality.passed:
            return {"success": True, "image": design_image, "quality": quality}

        # Auto-improve
        design_image = scorer.auto_improve_design(design_image, plan, quality)

        # Re-score
        quality = scorer.score_design(design_image, plan)

        if quality.passed:
            return {"success": True, "image": design_image, "quality": quality}

    return {"success": False, "quality": quality, "issues": quality.issues}
```

## 🧪 Testing

### Run Test Suite
```bash
python test_new_features.py
```

This will test:
1. Brand book parsing
2. Chat agent planning
3. Grid rendering
4. Quality scoring
5. Template validation (manual)

### Manual Testing

#### Test Brand Book Parser
```python
from app.core.brandbook_parser import parse_brand_book

result = parse_brand_book("sample_brandbook.txt")
print(result["tokens"]["color"])
```

#### Test Chat Agent
```python
from app.core.chat_agent_planner import chat_plan_design
from app.core.brand_brain import BrandTokens, BrandPolicies

tokens = BrandTokens.get_default_tokens()
policies = BrandPolicies.get_default_policies()

plan = chat_plan_design(
    "Create a LinkedIn post for our product launch",
    tokens,
    policies
)

print(plan.headline)
```

#### Test Grid Renderer
```python
from app.core.renderer_grid import GridRenderer

renderer = GridRenderer(tokens)
design = renderer.render_design(plan, background_url="https://...")
design.save("output.png")
```

## 📝 API Contracts

### DesignPlan
```python
@dataclass
class DesignPlan:
    headline: str              # Max 7 words
    subhead: str               # Max 16 words
    cta_text: str              # From whitelist
    visual_concept: str        # For image generation
    channel: str               # ig, fb, linkedin, twitter
    aspect_ratio: str          # 1x1, 4x5, 9x16, 16x9
    palette_mode: str          # primary, secondary, accent, mono
    background_style: str      # Detailed prompt
    logo_position: str         # TL, TR, BR, BL
    product_image_needed: bool
    reasoning: Optional[str]   # Why these choices
```

### QualityScore
```python
@dataclass
class QualityScore:
    overall_score: float        # 0-100
    passed: bool                # >= threshold
    dimensions: Dict[str, float]  # Individual scores
    issues: List[str]           # Problems found
    suggestions: List[str]      # How to fix
```

### TemplateValidationResult
```python
@dataclass
class TemplateValidationResult:
    template_id: str
    is_valid: bool
    has_autofill_fields: bool
    placeholder_fields: List[str]
    issues: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
```

## 🔌 Extending the System

### Add Custom Renderer
```python
class CustomRenderer(GridRenderer):
    """Your custom rendering logic"""

    def _apply_overlay(self, canvas, palette_mode):
        # Custom overlay logic
        return super()._apply_overlay(canvas, palette_mode)
```

### Add Custom Quality Dimension
```python
class EnhancedQualityScorer(DesignQualityScorer):
    """Add your own quality metrics"""

    def score_design(self, image, plan, metadata=None):
        result = super().score_design(image, plan, metadata)

        # Add custom dimension
        custom_score = self._score_custom_metric(image)
        result.dimensions['custom_metric'] = custom_score

        # Recalculate overall
        result.overall_score = self._recalculate_overall(result.dimensions)

        return result
```

## 🚀 Deployment Checklist

- [ ] Install dependencies: `pip install PyPDF2 pdfplumber python-docx Pillow`
- [ ] Test brand book parser with sample file
- [ ] Test chat agent with your brand
- [ ] Test grid renderer output
- [ ] Configure quality thresholds
- [ ] Add chat UI to navigation
- [ ] Set up async job queue for long-running generations
- [ ] Configure storage for rendered designs
- [ ] Add monitoring/logging
- [ ] Test Canva template validator
- [ ] Update user documentation

## 📚 Additional Resources

- **Sample Brand Book**: `sample_brandbook.txt`
- **Test Script**: `test_new_features.py`
- **Chat UI**: `app/pages/3_Chat_Create.py`
- **Existing Integrations**:
  - Canva Renderer: `app/core/renderer_canva.py`
  - Original Planner: `app/core/planner_v2.py`
  - Image Generator: `app/core/gen_openai.py`

## 🆘 Troubleshooting

### Issue: "No module named 'PyPDF2'"
**Solution**: `pip install PyPDF2 pdfplumber`

### Issue: "Font not found"
**Solution**: GridRenderer falls back to default fonts if system fonts unavailable

### Issue: "Template validator returns 403"
**Solution**: Ensure `brandtemplate:content:read` scope is enabled in Canva app

### Issue: "Quality score always fails"
**Solution**: Adjust `quality_threshold` parameter (default 70.0)

### Issue: "Chat agent doesn't return JSON"
**Solution**: The agent should auto-format. Check `extract_design_plan()` logs.

## 🎓 Next Steps

1. **Run the test script**: `python test_new_features.py`
2. **Try the chat UI**: Navigate to "Chat Create" page in Streamlit
3. **Upload a brand book**: Test the parser with `sample_brandbook.txt`
4. **Compare renderers**: Try both Canva and Grid renderers
5. **Tune quality scorer**: Adjust weights and thresholds for your needs

---

Built with ❤️ for human-quality design automation
