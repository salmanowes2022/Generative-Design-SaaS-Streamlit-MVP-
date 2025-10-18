# How to Create Canva Templates for Brand Brain v2

This guide explains how to create Canva templates that work with Brand Brain's autofill system.

## Template Contract

Each Canva template **must** expose these exact placeholder names:

### Required Placeholders

| Placeholder | Type | Description | Constraints |
|------------|------|-------------|-------------|
| `HEADLINE` | Text | Main headline | ≤7 words |
| `SUBHEAD` | Text | Supporting text | ≤16 words |
| `CTA_TEXT` | Text | Call-to-action | Must be in whitelist |
| `BG_IMAGE` | Image | AI-generated background | No text/logos |
| `PRIMARY_COLOR` | Color | Brand color overlay | From tokens |

### Optional Placeholders

| Placeholder | Type | Description |
|------------|------|-------------|
| `PRODUCT_IMAGE` | Image | Product photo |
| `LOGO` | Image | Brand logo (auto-placed) |

## Step-by-Step: Creating a Template

### 1. Design in Canva

1. Go to Canva.com and create a new design
2. Choose your dimensions:
   - **1080×1080px** (Instagram 1:1)
   - **1080×1350px** (Instagram 4:5)
   - **1080×1920px** (Instagram Story 9:16)
   - **1200×628px** (Facebook Post)

### 2. Add Text Placeholders

For each text element:

1. Add a text box
2. **Right-click → "Set as autofill placeholder"**
3. Name it exactly: `HEADLINE`, `SUBHEAD`, or `CTA_TEXT`
4. Style the text (font, size, color, alignment)
   - Headline: Bold, large (32-48pt)
   - Subhead: Regular, medium (14-18pt)
   - CTA: Button-like treatment

**Example Headline Setup:**
```
Text: "Your Headline Here"
Placeholder Name: HEADLINE
Font: Inter Bold
Size: 40pt
Color: #1F2937 (will be overridden by PRIMARY_COLOR)
Max Lines: 2
```

### 3. Add Image Placeholders

#### Background Image

1. Add a rectangle covering full canvas
2. **Right-click → "Set as autofill placeholder"**
3. Name: `BG_IMAGE`
4. Send to back (Ctrl/Cmd + Shift + [)

**Critical:** Reserve space for logo placement:
- If logo position is `top-right`: Keep top-right 200×150px area clean
- If logo position is `bottom-right`: Keep bottom-right 200×150px area clean

#### Product Image (Optional)

1. Add an image placeholder
2. Name: `PRODUCT_IMAGE`
3. Position strategically (usually center or left third)
4. Apply styling (shadow, border, mask)

### 4. Add Color Placeholder

1. Add a shape (rectangle, circle) that uses the primary brand color
2. **Right-click → "Set as autofill placeholder"**
3. Name: `PRIMARY_COLOR`
4. This could be:
   - Accent bar
   - Text highlight background
   - Button background
   - Border color

### 5. Design Logo Safe Zone

**Important:** Don't place a logo directly in the template. Brand Brain will add it dynamically.

Instead, design with logo placement in mind:

```
┌─────────────────────────────┐
│ [Safe Zone]                 │  ← 40px margin
│                             │
│    HEADLINE                 │
│    Subhead text here        │
│                             │
│    [Product Image]          │
│                             │
│                    [Logo]   │  ← Reserve this space
│                             │
└─────────────────────────────┘
```

### 6. Test Composition

Use these example values to test:

- **HEADLINE:** "New Product Launch"
- **SUBHEAD:** "Discover our latest innovation"
- **CTA_TEXT:** "Learn More"
- **BG_IMAGE:** Upload a clean stock photo
- **PRIMARY_COLOR:** #4F46E5

Ensure:
- Text is readable at all sizes
- Background image doesn't compete with text
- Logo area remains uncluttered
- CTA button stands out

### 7. Save as Template

1. Click **"Use as template"**
2. Set permissions: **"Anyone with link can use"**
3. Copy the template ID from URL:
   ```
   https://www.canva.com/design/ABC123XYZ/...
                                    ^^^^^^^^^ This is your template_id
   ```

### 8. Register Template

Add to `brand_kits.tokens.templates`:

```json
{
  "templates": {
    "ig_1x1": "ABC123XYZ",
    "ig_4x5": "DEF456UVW",
    "ig_9x16": "GHI789RST"
  }
}
```

## Best Practices

### Layout

✅ **Do:**
- Use grid system (12 columns)
- Leave generous white space
- Align elements to grid
- Reserve logo safe zone (40px minimum)

❌ **Don't:**
- Overcrowd the design
- Place text over busy backgrounds
- Use more than 2-3 fonts
- Ignore safe zones

### Typography

✅ **Do:**
- Use brand fonts from tokens
- Maintain clear hierarchy (headline > subhead > CTA)
- Ensure WCAG AA contrast (4.5:1 minimum)
- Limit headline to 2 lines

❌ **Don't:**
- Use decorative fonts for body text
- Make text too small (<14pt)
- Use all caps for long text
- Overlay text on complex images without treatment

### Colors

✅ **Do:**
- Use PRIMARY_COLOR for accents
- Maintain brand consistency
- Test with all palette modes (primary/secondary/accent/mono)
- Ensure text contrast

❌ **Don't:**
- Hard-code brand colors (use placeholders)
- Use colors outside brand palette
- Forget about color-blind users

### Images

✅ **Do:**
- Design for various image styles
- Use masks/frames for product images
- Blur or darken background images under text
- Test with both light and dark backgrounds

❌ **Don't:**
- Assume background will always be light
- Rely on specific image content
- Forget aspect ratio variations

## Template Variations

### Promo Template (Product-focused)

```
Layout:
- Large product image (left 60%)
- Text block (right 40%)
- CTA button at bottom
- Logo in top-right

Placeholders:
- BG_IMAGE (blurred, low opacity)
- PRODUCT_IMAGE (featured)
- HEADLINE
- SUBHEAD
- CTA_TEXT
- PRIMARY_COLOR (CTA button)
```

### Announcement Template (Text-focused)

```
Layout:
- Full-bleed background image
- Centered text block
- Badge/label with PRIMARY_COLOR
- Logo in corner

Placeholders:
- BG_IMAGE (full canvas)
- HEADLINE (large, centered)
- SUBHEAD (centered)
- CTA_TEXT (button)
- PRIMARY_COLOR (badge)
```

### Quote Template (Minimal)

```
Layout:
- Clean background
- Large centered quote (HEADLINE)
- Attribution (SUBHEAD)
- Subtle CTA
- Logo small in corner

Placeholders:
- BG_IMAGE (solid or subtle gradient)
- HEADLINE (quote marks)
- SUBHEAD (author)
- CTA_TEXT (subtle)
- PRIMARY_COLOR (quote marks or underline)
```

## Testing Your Template

### 1. Manual Test in Canva

Use Canva's autofill preview:
1. Open template
2. Click **"Use template"**
3. Fill placeholders manually
4. Verify all elements update correctly

### 2. API Test

```python
from app.core.renderer_canva import canva_renderer
from app.core.brand_brain import brand_brain

# Load brand tokens
tokens = brand_brain.get_brand_brain(brand_kit_id)["tokens"]

# Test content
content = {
    "headline": "Test Headline",
    "subhead": "This is a test subhead",
    "cta_text": "Learn More",
    "bg_image_url": "https://example.com/test-bg.png",
    "palette_mode": "primary"
}

# Create design
result = canva_renderer.create_design(
    template_id="YOUR_TEMPLATE_ID",
    content=content,
    tokens=tokens,
    org_id=org_id
)

print(f"Success: {result['success']}")
print(f"Design URL: {result['design_url']}")
```

### 3. Validation Checklist

- [ ] All placeholders named correctly
- [ ] Text is readable (contrast check)
- [ ] Logo safe zone is clear
- [ ] Works with light and dark backgrounds
- [ ] Headline fits in 2 lines max
- [ ] CTA button is prominent
- [ ] Template ID added to tokens
- [ ] Tested with 3+ different images
- [ ] Tested with all palette modes
- [ ] Mobile preview looks good

## Troubleshooting

### "Placeholder not found"

**Problem:** Template missing required placeholder

**Solution:**
1. Open template in Canva
2. Right-click text/image → "Set as autofill placeholder"
3. Ensure exact name match (case-sensitive)

### "Text overflow"

**Problem:** Headline/subhead too long for text box

**Solution:**
1. Increase text box height
2. Enable "Auto-resize"
3. Set max lines to 2 (headline) or 3 (subhead)
4. Reduce font size slightly

### "Image doesn't fill"

**Problem:** Background image doesn't cover canvas

**Solution:**
1. Set image placeholder fill mode to "Fill"
2. Enable "Crop to fill"
3. Lock aspect ratio to canvas size

### "Colors look wrong"

**Problem:** PRIMARY_COLOR not applying correctly

**Solution:**
1. Check placeholder is named `PRIMARY_COLOR` exactly
2. Verify it's set as color placeholder (not text/image)
3. Test with hex values from brand tokens

### "Logo overlaps text"

**Problem:** Logo placed over important content

**Solution:**
1. Review your safe zone design
2. Adjust text position to respect logo area
3. Update `logo.allowed_positions` in tokens
4. Use `create_preview_with_safe_zone()` to visualize

## Advanced: Multi-page Templates

For templates with multiple pages (e.g., carousel):

1. Create each page as a separate template
2. Register as array in tokens:

```json
{
  "templates": {
    "ig_carousel": [
      "page1_template_id",
      "page2_template_id",
      "page3_template_id"
    ]
  }
}
```

3. Planner will generate content for each page
4. Renderer will create multi-page design

## Resources

- [Canva Autofill API Docs](https://www.canva.com/developers/docs/autofill/)
- [Brand Brain Architecture](../ARCHITECTURE_V2.md)
- [Design Token Reference](../app/core/brand_brain.py)

## Support

Questions? Issues?
- Check logs in `agent_audit` table
- Review validation errors in UI
- Contact: support@yourdomain.com
