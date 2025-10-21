"""
Brand Brain v2
Central intelligence for brand consistency, design tokens, and policy enforcement
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from dataclasses import dataclass
import json
from datetime import datetime

from app.infra.config import settings
from app.infra.db import get_db
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BrandTokens:
    """Design tokens extracted from brand guidelines"""
    color: Dict[str, Any]
    type: Dict[str, Any]
    logo: Dict[str, Any]
    layout: Dict[str, Any]
    templates: Dict[str, str]
    cta_whitelist: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrandTokens':
        """Create from JSON dict"""
        return cls(
            color=data.get('color', {}),
            type=data.get('type', {}),
            logo=data.get('logo', {}),
            layout=data.get('layout', {}),
            templates=data.get('templates', {}),
            cta_whitelist=data.get('cta_whitelist', [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON dict"""
        return {
            'color': self.color,
            'type': self.type,
            'logo': self.logo,
            'layout': self.layout,
            'templates': self.templates,
            'cta_whitelist': self.cta_whitelist
        }

    @classmethod
    def get_default_tokens(cls) -> 'BrandTokens':
        """Default tokens when brand book doesn't provide info"""
        return cls(
            color={
                "primary": "#4F46E5",
                "secondary": "#7C3AED",
                "accent": "#F59E0B",
                "background": "#FFFFFF",
                "text": "#111111",
                "min_contrast": 4.5
            },
            type={
                "heading": {
                    "family": "Inter",
                    "weights": [700],
                    "scale": [48, 36, 28]
                },
                "body": {
                    "family": "Inter",
                    "weights": [400],
                    "size": 16
                }
            },
            logo={
                "variants": [
                    {"name": "full", "path": "", "on": "light"}
                ],
                "min_px": 128,
                "safe_zone": "1x",
                "allowed_positions": ["TL", "TR", "BR"]
            },
            layout={
                "grid": 12,
                "spacing": 8,
                "radius": 16
            },
            templates={
                "ig_1x1": "tmpl_IG_1x1_v1",
                "ig_4x5": "tmpl_IG_4x5_promo_v1",
                "ig_9x16": "tmpl_IG_9x16_story_v1",
                "li_191x1": "tmpl_LI_191x1_banner_v1"
            },
            cta_whitelist=[
                "Get Started", "Try Free", "Learn More", "Join Now",
                "Sign Up", "Download", "Start Now", "Discover"
            ]
        )


@dataclass
class BrandPolicies:
    """Brand voice and content policies"""
    voice: List[str]
    forbid: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrandPolicies':
        """Create from JSON dict"""
        return cls(
            voice=data.get('voice', []),
            forbid=data.get('forbid', [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON dict"""
        return {
            'voice': self.voice,
            'forbid': self.forbid
        }

    @classmethod
    def get_default_policies(cls) -> 'BrandPolicies':
        """Default policies"""
        return cls(
            voice=["professional", "clear", "authentic"],
            forbid=["guaranteed", "revolutionary", "game-changing"]
        )


class BrandBrain:
    """
    Central brand intelligence system
    Manages design tokens, policies, and brand compliance
    """

    def __init__(self):
        self.db = get_db()

    def extract_tokens_from_guidelines(
        self,
        guidelines: Dict[str, Any],
        brand_name: str
    ) -> BrandTokens:
        """
        Extract design tokens from brand guidelines

        Args:
            guidelines: Parsed brand guidelines from PDF/analysis
            brand_name: Brand name

        Returns:
            BrandTokens with extracted or default values
        """
        logger.info(f"Extracting design tokens for {brand_name}")

        # Start with defaults
        tokens = BrandTokens.get_default_tokens()

        # Extract colors from visual_identity
        visual_id = guidelines.get('visual_identity', {})
        colors = visual_id.get('colors', {})

        if colors:
            # Map brand guidelines colors to tokens
            if colors.get('primary'):
                tokens.color['primary'] = colors['primary'].get('hex', tokens.color['primary'])
            if colors.get('secondary'):
                tokens.color['secondary'] = colors['secondary'].get('hex', tokens.color['secondary'])
            if colors.get('accent'):
                accent_colors = colors['accent']
                if isinstance(accent_colors, list) and len(accent_colors) > 0:
                    tokens.color['accent'] = accent_colors[0].get('hex', tokens.color['accent'])

        # Extract typography
        typography = visual_id.get('typography', {})
        if typography:
            heading = typography.get('heading_font', {})
            if heading.get('family'):
                tokens.type['heading']['family'] = heading['family']
            if heading.get('weights'):
                tokens.type['heading']['weights'] = heading['weights']

            body = typography.get('body_font', {})
            if body.get('family'):
                tokens.type['body']['family'] = body['family']

        # Extract logo rules
        logo_info = visual_id.get('logo', {})
        if logo_info:
            if logo_info.get('minimum_size'):
                # Parse minimum size (e.g., "128px" -> 128)
                min_size_str = logo_info['minimum_size']
                try:
                    tokens.logo['min_px'] = int(''.join(filter(str.isdigit, min_size_str)))
                except:
                    pass

            if logo_info.get('clear_space'):
                tokens.logo['safe_zone'] = logo_info['clear_space']

            if logo_info.get('placement_guidelines'):
                # Map placement guidelines to positions
                placements = logo_info['placement_guidelines']
                positions = []
                for p in placements:
                    p_lower = p.lower()
                    if 'top' in p_lower and 'right' in p_lower:
                        positions.append('TR')
                    elif 'top' in p_lower and 'left' in p_lower:
                        positions.append('TL')
                    elif 'bottom' in p_lower and 'right' in p_lower:
                        positions.append('BR')
                    elif 'bottom' in p_lower and 'left' in p_lower:
                        positions.append('BL')
                if positions:
                    tokens.logo['allowed_positions'] = positions

        # Extract layout from layout_system
        layout = guidelines.get('layout_system', {})
        if layout:
            grid_str = layout.get('grid', '')
            if grid_str:
                # Try to extract grid number (e.g., "12-column grid" -> 12)
                try:
                    tokens.layout['grid'] = int(''.join(filter(str.isdigit, grid_str)))
                except:
                    pass

            spacing = layout.get('spacing', {})
            if spacing:
                # Extract spacing value
                for key in ['margins', 'padding', 'gaps']:
                    if key in spacing:
                        try:
                            val = spacing[key]
                            tokens.layout['spacing'] = int(''.join(filter(str.isdigit, str(val))))
                            break
                        except:
                            pass

        # Extract CTAs from usage guidelines
        usage = guidelines.get('usage_guidelines', {})
        if usage.get('dos'):
            # Look for CTA examples in best practices
            for practice in usage['dos']:
                if any(word in practice.lower() for word in ['cta', 'call to action', 'button']):
                    # This is a CTA-related guideline, keep default whitelist
                    break

        logger.info(f"Extracted tokens: {tokens.to_dict()}")
        return tokens

    def extract_policies_from_guidelines(
        self,
        guidelines: Dict[str, Any],
        brand_name: str
    ) -> BrandPolicies:
        """
        Extract brand policies from guidelines

        Args:
            guidelines: Parsed brand guidelines
            brand_name: Brand name

        Returns:
            BrandPolicies with extracted or default values
        """
        logger.info(f"Extracting brand policies for {brand_name}")

        policies = BrandPolicies.get_default_policies()

        # Extract voice from brand_messaging
        messaging = guidelines.get('brand_messaging', {})
        if messaging:
            voice_traits = messaging.get('personality', [])
            if voice_traits:
                policies.voice = voice_traits[:5]  # Top 5 traits

            # Look for forbidden terms in usage guidelines
            usage = guidelines.get('usage_guidelines', {})
            if usage.get('donts'):
                # Extract forbidden terms from don'ts
                forbidden = []
                for dont in usage['donts']:
                    # Look for "don't say", "avoid", etc.
                    if any(word in dont.lower() for word in ['say', 'use', 'claim']):
                        # Extract the forbidden term
                        forbidden.append(dont)
                if forbidden:
                    policies.forbid = forbidden[:10]  # Top 10

        logger.info(f"Extracted policies: {policies.to_dict()}")
        return policies

    def save_brand_brain(
        self,
        brand_kit_id: UUID,
        tokens: BrandTokens,
        policies: BrandPolicies
    ) -> None:
        """
        Save brand brain (tokens + policies) to database

        Args:
            brand_kit_id: Brand kit UUID
            tokens: Design tokens
            policies: Brand policies
        """
        try:
            self.db.update(
                table='brand_kits',
                data={
                    'tokens': json.dumps(tokens.to_dict()),
                    'policies': json.dumps(policies.to_dict()),
                    'version': 2
                },
                where_clause='id = %s',
                where_params=(str(brand_kit_id),)
            )

            logger.info(f"Saved Brand Brain v2 for brand kit {brand_kit_id}")

        except Exception as e:
            logger.error(f"Error saving brand brain: {str(e)}")
            raise

    def get_brand_brain(
        self,
        brand_kit_id: UUID
    ) -> tuple[Optional[BrandTokens], Optional[BrandPolicies]]:
        """
        Retrieve brand brain from database

        Args:
            brand_kit_id: Brand kit UUID

        Returns:
            Tuple of (tokens, policies) or (None, None)
        """
        try:
            result = self.db.fetch_one(
                "SELECT tokens, policies FROM brand_kits WHERE id = %s",
                (str(brand_kit_id),)
            )

            if not result:
                return None, None

            tokens_data = result.get('tokens')
            policies_data = result.get('policies')

            tokens = None
            policies = None

            if tokens_data:
                if isinstance(tokens_data, str):
                    tokens_data = json.loads(tokens_data)
                tokens = BrandTokens.from_dict(tokens_data)

            if policies_data:
                if isinstance(policies_data, str):
                    policies_data = json.loads(policies_data)
                policies = BrandPolicies.from_dict(policies_data)

            return tokens, policies

        except Exception as e:
            logger.error(f"Error retrieving brand brain: {str(e)}")
            return None, None

    def audit_action(
        self,
        org_id: UUID,
        action: str,
        payload: Dict[str, Any],
        result: Dict[str, Any],
        duration_ms: Optional[int] = None,
        brand_kit_id: Optional[UUID] = None,
        asset_id: Optional[UUID] = None
    ) -> None:
        """
        Log an action to audit trail

        Args:
            org_id: Organization ID
            action: Action name (plan, render, validate, etc.)
            payload: Input data
            result: Output data
            duration_ms: Execution time
            brand_kit_id: Optional brand kit ID
            asset_id: Optional asset ID
        """
        try:
            self.db.insert(
                table='agent_audit',
                data={
                    'org_id': str(org_id),
                    'brand_kit_id': str(brand_kit_id) if brand_kit_id else None,
                    'asset_id': str(asset_id) if asset_id else None,
                    'action': action,
                    'payload': json.dumps(payload),
                    'result': json.dumps(result),
                    'duration_ms': duration_ms
                }
            )

            logger.debug(f"Audited action: {action} for org {org_id}")

        except Exception as e:
            logger.warning(f"Failed to audit action: {str(e)}")
            # Don't raise - auditing should not block main flow


# Singleton instance
brand_brain = BrandBrain()
