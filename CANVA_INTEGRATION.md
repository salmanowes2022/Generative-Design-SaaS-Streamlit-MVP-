# Canva Connect API Integration

Complete integration guide for the Canva Connect API with your Generative Design SaaS platform.

## Overview

This integration enables:
- **OAuth2 Authentication** - Secure user authorization with Canva
- **Brand Template Management** - Browse and configure Canva templates
- **Automated Design Creation** - Generate designs using AI + Canva templates
- **Design Export** - Export designs as high-quality images
- **User Profile & Designs** - Access user's Canva profile and designs

## Architecture

```
Streamlit UI
    ↓
OAuth Manager (canva_oauth.py) ← Handles authentication & tokens
    ↓
Canva Renderer (renderer_canva.py) ← Creates designs via Connect API
    ↓
Canva Connect API (api.canva.com/rest/v1)
```

## Prerequisites

### 1. Canva Developer Account

1. Go to [Canva Developers](https://www.canva.com/developers)
2. Create a new app
3. Note your **Client ID** and **Client Secret**

### 2. Configure Scopes

In your Canva app settings, enable these scopes:
- ✅ `asset:read` - Read assets
- ✅ `design:content:read` - Read design content
- ✅ `design:content:write` - Create and modify designs
- ✅ `design:meta:read` - Read design metadata
- ✅ `profile:read` - Read user profile

### 3. Set Redirect URI

In your Canva app settings, add this redirect URI:
```
http://localhost:8501/Canva_Callback
```

For production, update to your domain:
```
https://yourdomain.com/Canva_Callback
```

## Installation

### 1. Environment Variables

Add to your `.env` file:

```env
# Canva Configuration
CANVA_CLIENT_ID=your_client_id_here
CANVA_CLIENT_SECRET=your_client_secret_here
CANVA_REDIRECT_URI=http://localhost:8501/Canva_Callback
CANVA_API_BASE=https://api.canva.com/rest/v1
```

### 2. Database Migration

Run the migration to create the tokens table:

```bash
python run_migration.py
```

This creates the `canva_tokens` table to store OAuth tokens.

### 3. Install Dependencies

The integration uses existing dependencies:
- `requests` - HTTP client
- `streamlit` - UI framework
- `psycopg` - PostgreSQL driver

## Usage Guide

### For Users

#### 1. Connect Canva Account

1. Navigate to any page with Canva integration
2. Look for the sidebar section "🔗 Canva"
3. Click "Connect to Canva"
4. Authorize the app in the popup window
5. You'll be redirected back with success confirmation

#### 2. Configure Brand Templates

1. Go to **Canva Templates** page
2. Browse your available brand templates
3. Map templates to channels and aspect ratios:
   - Instagram 1:1 (Square)
   - Instagram 4:5 (Portrait)
   - Instagram 9:16 (Story)
   - Facebook 16:9 (Landscape)
   - etc.

#### 3. Generate Designs

1. Go to **Generate v2** page
2. Ensure Canva is connected (check sidebar)
3. Create a design plan via chat
4. Click "Create Design in Canva"
5. Wait for:
   - AI background generation
   - Canva design creation
   - Brand compliance validation
6. View and download your design!

### For Developers

#### OAuth Flow

```python
from app.core.canva_oauth import canva_oauth

# Check if user is authenticated
is_auth = canva_oauth.is_authenticated(user_id)

# Get access token
access_token = canva_oauth.get_access_token(user_id)

# Get authorization URL
auth_url = canva_oauth.get_authorization_url()

# Exchange code for token (in callback handler)
token_data = canva_oauth.exchange_code_for_token(code)
canva_oauth.save_token_to_db(user_id, token_data)
```

#### Creating Designs

```python
from app.core.renderer_canva import CanvaRenderer

# Initialize with token
renderer = CanvaRenderer(access_token=access_token)

# Prepare content
content = {
    "headline": "Your Headline Here",
    "subhead": "Supporting text goes here",
    "cta_text": "Shop Now",
    "bg_image_url": "https://example.com/background.png",
    "palette_mode": "primary"  # primary, secondary, accent, mono
}

# Create design
result = renderer.create_design(
    template_id="your_template_id",
    content=content,
    tokens=brand_tokens,
    org_id=org_id
)

# Access results
design_id = result["design_id"]
design_url = result["design_url"]  # Edit URL
export_url = result["export_url"]  # PNG download URL
```

#### Listing Templates

```python
# List brand templates
templates = renderer.list_brand_templates(limit=50)

for template in templates:
    print(f"Template: {template['name']}")
    print(f"ID: {template['id']}")
    print(f"Size: {template['width']}x{template['height']}")
```

#### User Profile

```python
# Get user profile
profile = renderer.get_user_profile()

print(f"Name: {profile['display_name']}")
print(f"Email: {profile['email']}")
```

## Template Placeholders

Your Canva templates must use these placeholder names:

### Text Placeholders
- `HEADLINE` - Main headline (max 7 words)
- `SUBHEAD` - Supporting text (max 16 words)
- `CTA_TEXT` - Call-to-action button text

### Image Placeholders
- `BG_IMAGE` - Background image (AI-generated)
- `PRODUCT_IMAGE` - Product image (optional)

### Color Placeholders
- `PRIMARY_COLOR` - Brand primary color (auto-filled based on palette_mode)

## File Structure

```
app/
├── core/
│   ├── canva_oauth.py           # OAuth2 authentication manager
│   ├── renderer_canva.py         # Canva Connect API renderer
│   └── ...
├── pages/
│   ├── 2_Generate_V2.py          # Main generation page (Canva integrated)
│   ├── 6_Canva_Templates.py      # Template management page
│   └── Canva_Callback.py         # OAuth callback handler
└── infra/
    └── config.py                 # Configuration with Canva settings

migrations/
└── create_canva_tokens_table.sql # Database schema

run_migration.py                  # Migration runner script
```

## API Endpoints Used

### Canva Connect API

- **POST /autofills** - Create design from template
- **POST /exports** - Export design as image
- **GET /exports/{job_id}** - Poll export job status
- **GET /designs** - List user designs
- **GET /brand-templates** - List brand templates
- **GET /users/me/profile** - Get user profile
- **POST /oauth/token** - Exchange code for token / Refresh token
- **POST /oauth/revoke** - Revoke token

## Security

### Token Storage

- Tokens are stored encrypted in PostgreSQL
- Access tokens automatically refresh when expired
- Tokens are tied to user accounts

### State Verification

- OAuth state parameter prevents CSRF attacks
- State is stored in session and verified on callback

### HTTPS Required

- In production, use HTTPS for all OAuth redirects
- Update `CANVA_REDIRECT_URI` to use `https://`

## Troubleshooting

### "Invalid scope" Error

**Problem:** Scopes requested don't match app configuration

**Solution:**
1. Check your Canva app settings
2. Ensure all required scopes are enabled
3. Update `canva_oauth.py` scopes if needed
4. Reconnect your account

### "Template not found" Error

**Problem:** Template ID doesn't exist or user doesn't have access

**Solution:**
1. Go to Canva Templates page
2. Browse available templates
3. Add template mappings for each channel

### "Token expired" Error

**Problem:** Access token expired and refresh failed

**Solution:**
1. Disconnect from Canva (sidebar)
2. Reconnect to get new tokens
3. Check that refresh token is being stored

### Export Timeout

**Problem:** Design export takes too long

**Solution:**
1. Check Canva API status
2. Increase `max_attempts` in `_poll_export_job`
3. Simplify template design

## Limits & Quotas

### Canva Connect API Limits

- **Rate Limits:** Check your app's rate limits in Canva dashboard
- **Design Size:** Maximum 25MB per design
- **Export Format:** PNG, JPG, PDF supported
- **Templates:** Unlimited brand templates

### Recommendations

- Cache template lists (refresh periodically)
- Implement rate limit backoff
- Monitor token expiration proactively
- Use webhooks for long-running exports (future enhancement)

## Testing

### Manual Testing

1. **OAuth Flow:**
   ```bash
   # Start Streamlit app
   streamlit run app/streamlit_app.py

   # Navigate to Canva Templates page
   # Click "Connect to Canva"
   # Verify successful authorization
   ```

2. **Design Creation:**
   ```bash
   # Navigate to Generate V2 page
   # Create a design plan
   # Click "Create Design in Canva"
   # Verify design is created and exported
   ```

3. **Template Management:**
   ```bash
   # Navigate to Canva Templates page
   # Browse templates
   # Add template mappings
   # Verify mappings saved to Brand Brain
   ```

### Automated Testing

```python
# Test OAuth flow
def test_oauth_flow():
    from app.core.canva_oauth import canva_oauth

    # Generate auth URL
    auth_url = canva_oauth.get_authorization_url()
    assert "oauth/authorize" in auth_url
    assert "client_id" in auth_url

    # Exchange code (use mock)
    # token_data = canva_oauth.exchange_code_for_token(code)
    # assert "access_token" in token_data

# Test renderer
def test_renderer():
    from app.core.renderer_canva import CanvaRenderer

    renderer = CanvaRenderer(access_token="test_token")
    assert renderer.api_base == "https://api.canva.com/rest/v1"
```

## Future Enhancements

### Planned Features

1. **Webhook Integration**
   - Real-time notifications for export completion
   - Design collaboration events

2. **Bulk Operations**
   - Create multiple designs at once
   - Batch export

3. **Advanced Templates**
   - Multi-page designs
   - Animated designs
   - Video templates

4. **Team Features**
   - Shared brand templates
   - Team workspace integration
   - Approval workflows

5. **Analytics**
   - Track template performance
   - Design usage metrics
   - A/B testing

## Support

### Resources

- [Canva Connect API Docs](https://www.canva.com/developers/docs/connect-api)
- [OAuth 2.0 Spec](https://oauth.net/2/)
- [Streamlit Docs](https://docs.streamlit.io)

### Getting Help

1. Check the [Canva Developers Community](https://community.canva.com)
2. Review API error responses for details
3. Check application logs in `app/logs/`
4. Contact Canva support for API issues

## Contributors

Built with:
- Canva Connect API
- Streamlit
- Python 3.9+
- PostgreSQL

---

**Last Updated:** 2025-01-19

For questions or issues, please check the main README or contact support.
