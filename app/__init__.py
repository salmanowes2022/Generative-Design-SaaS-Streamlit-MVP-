"""
Streamlit Pages Package
Multi-page application for Brand Asset Generator
"""

# Page metadata
PAGES = {
    "onboard": {
        "title": "Onboard Brand Kit",
        "icon": "🏁",
        "description": "Upload logos, fonts, and define brand guidelines"
    },
    "generate": {
        "title": "Generate",
        "icon": "🎨",
        "description": "Create AI-generated images with brand context"
    },
    "compose": {
        "title": "Compose & Validate",
        "icon": "🧱",
        "description": "Apply brand overlay and validate composition"
    },
    "library": {
        "title": "Library",
        "icon": "📚",
        "description": "Browse and manage all generated assets"
    },
    "billing": {
        "title": "Billing",
        "icon": "💳",
        "description": "Manage subscription and view usage"
    }
}

__all__ = ["PAGES"]