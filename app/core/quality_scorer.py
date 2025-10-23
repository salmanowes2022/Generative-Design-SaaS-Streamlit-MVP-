"""
Quality Scorer
Automated design quality validation and scoring
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import io

from app.core.schemas_v2 import QualityScore, ScoreCategory, BrandTokensV2
from app.core.contrast_manager import contrast_manager
from app.core.chat_agent_planner import DesignPlan
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DesignMetrics:
    """Extracted metrics from design"""
    text_regions: List[Dict[str, Any]]
    color_usage: Dict[str, int]  # Color -> pixel count
    average_brightness: float  # 0-1
    contrast_ratios: List[float]
    has_logo: bool
    has_cta: bool
    text_size_avg: float  # Estimated average text size


class QualityScorer:
    """
    Automated design quality assessment

    Scoring Categories:
    - Readability (30%): Text contrast, size, hierarchy
    - Brand Consistency (25%): Color compliance, font usage
    - Composition (20%): Balance, whitespace, alignment
    - Impact (15%): Visual hierarchy, CTA prominence
    - Accessibility (10%): WCAG compliance, alt text
    """

    # Scoring weights
    WEIGHTS = {
        "readability": 0.30,
        "brand_consistency": 0.25,
        "composition": 0.20,
        "impact": 0.15,
        "accessibility": 0.10
    }

    def __init__(self, brand_tokens: Optional[BrandTokensV2] = None):
        """
        Initialize scorer

        Args:
            brand_tokens: Brand tokens for consistency checking
        """
        self.brand_tokens = brand_tokens or BrandTokensV2.get_default_tokens()

    def score_design(
        self,
        design_plan: DesignPlan,
        rendered_image: Optional[Image.Image] = None,
        design_url: Optional[str] = None
    ) -> QualityScore:
        """
        Score a complete design

        Args:
            design_plan: Design plan used to create design
            rendered_image: PIL Image of rendered design
            design_url: URL to rendered design (alternative to image)

        Returns:
            QualityScore with breakdown
        """
        logger.info("Scoring design quality...")

        # Score each category
        readability = self._score_readability(design_plan, rendered_image)
        brand_consistency = self._score_brand_consistency(design_plan)
        composition = self._score_composition(design_plan, rendered_image)
        impact = self._score_impact(design_plan)
        accessibility = self._score_accessibility(design_plan)

        # Calculate overall score
        overall = (
            readability.score * self.WEIGHTS["readability"] +
            brand_consistency.score * self.WEIGHTS["brand_consistency"] +
            composition.score * self.WEIGHTS["composition"] +
            impact.score * self.WEIGHTS["impact"] +
            accessibility.score * self.WEIGHTS["accessibility"]
        )

        overall = int(overall)

        # Generate suggestions
        suggestions = self._generate_suggestions(
            readability, brand_consistency, composition, impact, accessibility
        )

        logger.info(f"Overall quality score: {overall}/100")

        return QualityScore(
            overall_score=overall,
            readability=readability,
            brand_consistency=brand_consistency,
            composition=composition,
            impact=impact,
            accessibility=accessibility,
            suggestions=suggestions
        )

    def _score_readability(
        self,
        plan: DesignPlan,
        image: Optional[Image.Image]
    ) -> ScoreCategory:
        """Score readability (text contrast, size, hierarchy)"""
        score = 100
        issues = []

        # Check headline length
        headline_words = len(plan.headline.split())
        if headline_words > 7:
            score -= 10
            issues.append(f"Headline too long ({headline_words} words, recommend max 7)")

        # Check subhead length
        subhead_words = len(plan.subhead.split())
        if subhead_words > 16:
            score -= 10
            issues.append(f"Subhead too long ({subhead_words} words, recommend max 16)")

        # Check contrast (if we have access to colors)
        # In a real implementation, we'd analyze the rendered image
        # For now, do basic checks based on palette mode
        if plan.palette_mode == "mono":
            # Monochrome can have contrast issues
            score -= 5
            issues.append("Monochrome palette may reduce visual interest")

        # Check CTA text length
        if len(plan.cta_text) > 20:
            score -= 5
            issues.append("CTA text too long, should be punchy")

        # Text hierarchy score (headline should be distinct)
        if headline_words > 0 and subhead_words > 0:
            # Good hierarchy
            pass
        else:
            score -= 10
            issues.append("Missing text hierarchy (headline or subhead)")

        logger.info(f"Readability score: {score}/100")
        return ScoreCategory(score=max(0, score), issues=issues)

    def _score_brand_consistency(self, plan: DesignPlan) -> ScoreCategory:
        """Score brand consistency (colors, fonts, voice)"""
        score = 100
        issues = []

        # Check CTA against whitelist
        if self.brand_tokens.policies:
            approved_ctas = self.brand_tokens.policies.cta_whitelist
            if approved_ctas and plan.cta_text not in approved_ctas:
                score -= 20
                issues.append(f"CTA '{plan.cta_text}' not in approved list")

        # Check for forbidden terms (in headline/subhead)
        if self.brand_tokens.policies:
            forbidden = self.brand_tokens.policies.forbidden_terms
            text = f"{plan.headline} {plan.subhead}".lower()

            for term in forbidden:
                if term.lower() in text:
                    score -= 15
                    issues.append(f"Contains forbidden term: '{term}'")

        # Check logo position
        if self.brand_tokens.logo:
            allowed_positions = self.brand_tokens.logo.allowed_positions
            if plan.logo_position not in allowed_positions:
                score -= 10
                issues.append(f"Logo position '{plan.logo_position}' not recommended")

        # Check palette mode usage
        if plan.palette_mode not in ["primary", "secondary", "accent"]:
            score -= 5
            issues.append(f"Unusual palette mode: {plan.palette_mode}")

        logger.info(f"Brand consistency score: {score}/100")
        return ScoreCategory(score=max(0, score), issues=issues)

    def _score_composition(
        self,
        plan: DesignPlan,
        image: Optional[Image.Image]
    ) -> ScoreCategory:
        """Score composition (balance, whitespace, alignment)"""
        score = 100
        issues = []

        # Check aspect ratio for channel
        optimal_ratios = {
            "ig": ["1x1", "4x5", "9x16"],
            "fb": ["1x1", "16x9"],
            "linkedin": ["1x1", "191x1"],
            "twitter": ["16x9", "1x1"]
        }

        if plan.channel in optimal_ratios:
            if plan.aspect_ratio not in optimal_ratios[plan.channel]:
                score -= 10
                issues.append(f"Non-optimal aspect ratio for {plan.channel}")

        # Check visual concept quality
        concept_words = len(plan.visual_concept.split())
        if concept_words < 5:
            score -= 10
            issues.append("Visual concept too vague, needs more detail")
        elif concept_words > 50:
            score -= 5
            issues.append("Visual concept overly complex")

        # Background style check
        if not plan.background_style or len(plan.background_style) < 10:
            score -= 15
            issues.append("Background style description insufficient")

        # Check for balanced content
        total_words = (
            len(plan.headline.split()) +
            len(plan.subhead.split()) +
            len(plan.cta_text.split())
        )

        if total_words < 5:
            score -= 10
            issues.append("Too little text content")
        elif total_words > 30:
            score -= 10
            issues.append("Too much text content, may feel crowded")

        logger.info(f"Composition score: {score}/100")
        return ScoreCategory(score=max(0, score), issues=issues)

    def _score_impact(self, plan: DesignPlan) -> ScoreCategory:
        """Score impact (visual hierarchy, CTA prominence)"""
        score = 100
        issues = []

        # Check CTA strength
        weak_ctas = ["click here", "submit", "ok", "next"]
        if plan.cta_text.lower() in weak_ctas:
            score -= 20
            issues.append(f"Weak CTA: '{plan.cta_text}'. Use action-oriented text")

        # Check headline impact
        if not any(char.isupper() for char in plan.headline):
            score -= 10
            issues.append("Headline lacks emphasis (no caps)")

        # Check for urgency/value in text
        urgency_words = ["now", "today", "limited", "exclusive", "save", "free"]
        text = f"{plan.headline} {plan.subhead} {plan.cta_text}".lower()

        has_urgency = any(word in text for word in urgency_words)
        if not has_urgency and plan.channel in ["ig", "fb"]:
            score -= 5
            issues.append("Consider adding urgency/value to drive action")

        # Check visual concept appeal
        appeal_keywords = ["vibrant", "professional", "authentic", "dynamic", "striking"]
        has_appeal = any(word in plan.visual_concept.lower() for word in appeal_keywords)

        if not has_appeal:
            score -= 5
            issues.append("Visual concept could be more impactful")

        logger.info(f"Impact score: {score}/100")
        return ScoreCategory(score=max(0, score), issues=issues)

    def _score_accessibility(self, plan: DesignPlan) -> ScoreCategory:
        """Score accessibility (WCAG compliance)"""
        score = 100
        issues = []

        # Simulate contrast check (in real impl, would check rendered image)
        # For now, make assumptions based on palette mode

        # Check text on image background
        # Dark backgrounds generally safer
        if plan.palette_mode in ["mono", "primary"]:
            # Likely dark overlay
            pass
        else:
            # Might have contrast issues
            score -= 10
            issues.append("Light palette mode may cause contrast issues on images")

        # Check for alt text (conceptual - would be in metadata)
        if not plan.visual_concept or len(plan.visual_concept) < 20:
            score -= 10
            issues.append("Insufficient visual description for alt text")

        # Logo contrast
        if plan.logo_position in ["TL", "TR"]:
            # Top positions - might conflict with light backgrounds
            pass

        # Check CTA visibility
        # CTA should use accent color for prominence
        if plan.palette_mode != "accent":
            score -= 5
            issues.append("CTA should use accent color for maximum visibility")

        logger.info(f"Accessibility score: {score}/100")
        return ScoreCategory(score=max(0, score), issues=issues)

    def _generate_suggestions(
        self,
        readability: ScoreCategory,
        brand_consistency: ScoreCategory,
        composition: ScoreCategory,
        impact: ScoreCategory,
        accessibility: ScoreCategory
    ) -> List[str]:
        """Generate actionable improvement suggestions"""
        suggestions = []

        # Priority: Fix failing categories first
        categories = [
            ("Readability", readability),
            ("Brand Consistency", brand_consistency),
            ("Composition", composition),
            ("Impact", impact),
            ("Accessibility", accessibility)
        ]

        # Sort by score (lowest first)
        categories.sort(key=lambda x: x[1].score)

        # Top 3 issues
        for name, category in categories[:3]:
            if category.issues:
                # Add first issue from each failing category
                suggestions.append(f"**{name}:** {category.issues[0]}")

        # Generic suggestions if score is low
        if readability.score < 80:
            suggestions.append("Consider using larger, bolder fonts for better readability")

        if brand_consistency.score < 80:
            suggestions.append("Review brand guidelines to ensure compliance")

        if impact.score < 80:
            suggestions.append("Strengthen CTA with action-oriented language")

        # Limit to top 5 suggestions
        return suggestions[:5]

    def quick_score(self, plan: DesignPlan) -> int:
        """
        Quick overall score without detailed breakdown

        Args:
            plan: Design plan

        Returns:
            Overall score (0-100)
        """
        full_score = self.score_design(plan)
        return full_score.overall_score


# Singleton instance (stateless, can use globally)
def score_design(plan: DesignPlan, brand_tokens: Optional[BrandTokensV2] = None) -> QualityScore:
    """
    Convenience function to score a design

    Args:
        plan: Design plan
        brand_tokens: Brand tokens for consistency checking

    Returns:
        QualityScore
    """
    scorer = QualityScorer(brand_tokens)
    return scorer.score_design(plan)
