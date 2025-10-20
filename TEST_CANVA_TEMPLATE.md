# Test Your Canva Template Integration

## Your Template
- **URL:** https://www.canva.com/design/DAG2VuRr1IU/y54M8HHeMh_hW1hwaTo3Jg/view
- **Design ID:** `DAG2VuRr1IU`

## How to Test It

### Option 1: Test via Streamlit Generate V2 Page

1. Go to the **Generate V2** page in your Streamlit app
2. Make sure you're **Connected to Canva** (you are! ✅)
3. Enter a design prompt, for example:
   ```
   Create a social media post for a summer sale with 20% off
   ```
4. Click **Generate Design**
5. The app will:
   - Use AI to plan the design
   - Generate a background image
   - Create the design in Canva using your template

### Option 2: Test Directly with Python

```python
from app.core.canva_oauth_bridge import canva_oauth_bridge
from app.core.renderer_canva import CanvaRenderer

# Get access token
access_token = canva_oauth_bridge.get_access_token()

# Initialize renderer
renderer = CanvaRenderer(access_token=access_token)

# Test autofill with your template
design_url = renderer.autofill_design(
    design_id="DAG2VuRr1IU",  # Your template ID
    data={
        "headline": "Summer Sale!",
        "body": "Get 20% off all items",
        "cta": "Shop Now"
    },
    image_url="https://example.com/summer-image.jpg"  # Replace with actual image
)

print(f"Design created: {design_url}")
```

## What Your Template Should Have

For the autofill to work, your Canva template needs to have **placeholders** with specific names:

### Text Placeholders:
- `{headline}` - Main headline
- `{body}` - Body text
- `{cta}` - Call-to-action button text

### Image Placeholders:
- Background image placeholder that can be replaced

## Next Steps

### 1. Configure Template in Brand Kit

You can add your template to the brand kit's token configuration:

```python
# In your Brand Brain tokens
tokens = {
    "templates": [
        {
            "id": "DAG2VuRr1IU",
            "name": "Social Media Post",
            "type": "instagram_post",
            "aspect_ratio": "1:1"
        }
    ],
    # ... other tokens
}
```

### 2. Test the Full Flow

1. **Generate V2 Page**: Try generating a design
2. **Monitor logs**: Check terminal for any errors
3. **Check Canva**: See if the design appears in your Canva account

## Troubleshooting

### If autofill doesn't work:

1. **Check template has placeholders**: Open your template in Canva and verify it has text fields named `{headline}`, `{body}`, etc.

2. **Check access token**: Make sure you're still connected to Canva

3. **Check design permissions**: Your template needs to be in your Canva account (not someone else's)

### Common Issues:

- **"Design not found"**: The design ID is incorrect or you don't have access
- **"Placeholders not found"**: The template doesn't have the expected placeholder names
- **"Unauthorized"**: Your Canva token expired - reconnect to Canva

## What's Next?

With Canva OAuth integration complete, you can now:

✅ **Generate designs programmatically**
✅ **Autofill templates with AI-generated content**
✅ **Create brand-consistent designs automatically**
✅ **Export designs as images or PDFs**

---

**Ready to test! Try generating a design in the Generate V2 page!** 🚀
