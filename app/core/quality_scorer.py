"""
Design Quality Scorer
Evaluates design quality across multiple dimensions
Provides actionable feedback for automatic improvements
"""
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
import io
import requests

try:
    from PIL import Image, ImageStat, ImageDraw, ImageFont
except ImportError:
    raise ImportError("Pillow required")

from app.core.brand_brain import BrandTokens
from app.core.chat_agent_planner import DesignPlan
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QualityScore:
    """Quality evaluation result"""
    overall_score: float  # 0-100
    passed: bool  # True if score >= threshold
    dimensions: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "overall_score": self.overall_score,
            "passed": self.passed,
            "dimensions": self.dimensions,
            "issues": self.issues,
            "suggestions": self.suggestions
        }


class DesignQualityScorer:
    """
    Multi-dimensional design quality evaluator

    Evaluates:
    - Text contrast (readability)
    - CTA prominence (visibility)
    - Layout balance (composition)
    - Brand accuracy (guideline adherence)
    - Visual hierarchy (focus flow)
    """

    def __init__(
        self,
        tokens: BrandTokens,
        quality_threshold: float = 70.0
    ):
        """
        Initialize scorer

        Args:
            tokens: Brand design tokens
            quality_threshold: Minimum acceptable score (0-100)
        """
        self.tokens = tokens
        self.threshold = quality_threshold

        # Scoring weights
        self.weights = {
            'text_contrast': 0.30,
            'cta_prominence': 0.25,
            'layout_balance': 0.20,
            'brand_accuracy': 0.15,
            'visual_hierarchy': 0.10
        }

    def score_design(
        self,
        image: Image.Image,
        plan: DesignPlan,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate design quality

        Args:
            image: Rendered design (PIL Image)
            plan: Original design plan
            metadata: Optional metadata (element positions, etc.)

        Returns:
            QualityScore with detailed feedback
        """
        logger.info("Scoring design quality...")

        scores = {}
        issues = []
        suggestions = []

        # 1. Text Contrast
        contrast_score, contrast_issues = self._score_text_contrast(image, plan, metadata)
        scores['text_contrast'] = contrast_score
        issues.extend(contrast_issues)

        # 2. CTA Prominence
        cta_score, cta_issues = self._score_cta_prominence(image, plan, metadata)
        scores['cta_prominence'] = cta_score
        issues.extend(cta_issues)

        # 3. Layout Balance
        balance_score, balance_issues = self._score_layout_balance(image)
        scores['layout_balance'] = balance_score
        issues.extend(balance_issues)

        # 4. Brand Accuracy
        brand_score, brand_issues = self._score_brand_accuracy(plan)
        scores['brand_accuracy'] = brand_score
        issues.extend(brand_issues)

        # 5. Visual Hierarchy
        hierarchy_score, hierarchy_issues = self._score_visual_hierarchy(image, plan)
        scores['visual_hierarchy'] = hierarchy_score
        issues.extend(hierarchy_issues)

        # Calculate weighted overall score
        overall = sum(
            scores[dim] * self.weights[dim]
            for dim in scores
        )

        # Generate suggestions based on issues
        suggestions = self._generate_suggestions(scores, issues)

        result = QualityScore(
            overall_score=round(overall, 2),
            passed=overall >= self.threshold,
            dimensions=scores,
            issues=issues,
            suggestions=suggestions
        )

        logger.info(f"Quality score: {result.overall_score}/100 ({'PASS' if result.passed else 'FAIL'})")
        return result

    def _score_text_contrast(
        self,
        image: Image.Image,
        plan: DesignPlan,
        metadata: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """
        Evaluate text-background contrast

        Returns: (score 0-100, list of issues)
        """
        issues = []

        # Sample background luminance from key text regions
        # For now, use simple heuristic: check bottom third where text usually is
        width, height = image.size
        text_region = image.crop((0, int(height * 0.66), width, height))

        # Calculate average luminance
        stat = ImageStat.Stat(text_region.convert('L'))
        avg_luminance = stat.mean[0]  # 0-255

        # Check if background is too light or too dark for white text
        # Ideal contrast: dark background (0-100) or light background with overlay
        if avg_luminance < 100:
            # Dark background - good for white text
            score = 100
        elif avg_luminance > 200:
            # Very light background - poor contrast
            score = 30
            issues.append("Low text contrast: background too light for white text")
        else:
            # Medium - acceptable with overlay
            score = 70

        # Check if minimum contrast ratio is met
        min_contrast = self.tokens.color.get('min_contrast', 4.5)
        if score < 70:
            issues.append(f"Text contrast below {min_contrast}:1 ratio requirement")

        return score, issues

    def _score_cta_prominence(
        self,
        image: Image.Image,
        plan: DesignPlan,
        metadata: Optional[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """
        Evaluate CTA button visibility and prominence

        Returns: (score 0-100, list of issues)
        """
        issues = []

        # Check if CTA uses brand accent color (high visibility)
        accent_color = self.tokens.color.get('accent', '#F59E0B')

        # Heuristic: if accent color is bright, CTA should be visible
        # For now, assume CTA is properly styled (we control the renderer)
        score = 85

        # Check CTA text length (should be short and punchy)
        cta_words = len(plan.cta_text.split())
        if cta_words > 3:
            score -= 20
            issues.append(f"CTA text too long: {cta_words} words (max 3 recommended)")

        # Check if CTA is in approved whitelist
        if self.tokens.cta_whitelist and plan.cta_text not in self.tokens.cta_whitelist:
            score -= 30
            issues.append(f"CTA '{plan.cta_text}' not in brand approved list")

        return max(0, score), issues

    def _score_layout_balance(self, image: Image.Image) -> Tuple[float, List[str]]:
        """
        Evaluate overall layout balance and composition

        Uses Rule of Thirds analysis
        """
        issues = []

        # Convert to grayscale for analysis
        gray = image.convert('L')
        width, height = gray.size

        # Divide into 9 zones (rule of thirds)
        third_w = width // 3
        third_h = height // 3

        zones = []
        for row in range(3):
            for col in range(3):
                x1 = col * third_w
                y1 = row * third_h
                x2 = x1 + third_w
                y2 = y1 + third_h
                zone = gray.crop((x1, y1, x2, y2))
                stat = ImageStat.Stat(zone)
                zones.append(stat.mean[0])

        # Check for balance: zones shouldn't be too different
        zone_variance = max(zones) - min(zones)

        if zone_variance < 50:
            # Too uniform - boring
            score = 60
            issues.append("Layout lacks visual interest: too uniform")
        elif zone_variance > 200:
            # Too unbalanced
            score = 65
            issues.append("Layout unbalanced: high variance across regions")
        else:
            # Good balance
            score = 95

        return score, issues

    def _score_brand_accuracy(self, plan: DesignPlan) -> Tuple[float, List[str]]:
        """
        Evaluate adherence to brand guidelines

        Checks:
        - Headline word count
        - Subhead word count
        - CTA in whitelist
        - Forbidden terms
        """
        issues = []
        score = 100

        # Headline length
        headline_words = len(plan.headline.split())
        if headline_words > 7:
            score -= 15
            issues.append(f"Headline too long: {headline_words} words (max 7)")

        # Subhead length
        subhead_words = len(plan.subhead.split())
        if subhead_words > 16:
            score -= 15
            issues.append(f"Subhead too long: {subhead_words} words (max 16)")

        # CTA whitelist
        if self.tokens.cta_whitelist:
            if plan.cta_text not in self.tokens.cta_whitelist:
                score -= 30
                issues.append(f"CTA '{plan.cta_text}' not approved")

        # Check for placeholder text
        placeholders = ['Lorem ipsum', 'Your text here', 'Placeholder']
        all_text = f"{plan.headline} {plan.subhead} {plan.cta_text}".lower()
        for placeholder in placeholders:
            if placeholder.lower() in all_text:
                score -= 40
                issues.append(f"Placeholder text detected: '{placeholder}'")

        return max(0, score), issues

    def _score_visual_hierarchy(
        self,
        image: Image.Image,
        plan: DesignPlan
    ) -> Tuple[float, List[str]]:
        """
        Evaluate visual hierarchy and focus flow

        Checks if:
        - Headline is prominent
        - CTA is visible
        - Layout guides eye naturally
        """
        issues = []

        # Simplified heuristic: check if bottom third (text area) has sufficient contrast
        width, height = image.size
        bottom_third = image.crop((0, int(height * 0.66), width, height))

        # Convert to grayscale
        gray = bottom_third.convert('L')
        stat = ImageStat.Stat(gray)

        # Standard deviation indicates variation (good for hierarchy)
        std_dev = stat.stddev[0]

        if std_dev < 30:
            score = 60
            issues.append("Weak visual hierarchy: text area lacks contrast variation")
        elif std_dev > 80:
            score = 95
        else:
            score = 80

        return score, issues

    def _generate_suggestions(
        self,
        scores: Dict[str, float],
        issues: List[str]
    ) -> List[str]:
        """Generate actionable suggestions based on scores"""
        suggestions = []

        # Text contrast suggestions
        if scores.get('text_contrast', 100) < 70:
            suggestions.append("Apply darker overlay gradient to improve text readability")
            suggestions.append("Consider using drop shadow on headline text")

        # CTA suggestions
        if scores.get('cta_prominence', 100) < 70:
            suggestions.append("Increase CTA button size or use brighter accent color")
            suggestions.append("Add more padding around CTA button")

        # Layout suggestions
        if scores.get('layout_balance', 100) < 70:
            suggestions.append("Adjust element positions to balance composition")
            suggestions.append("Consider adding a focal point to guide viewer's eye")

        # Brand accuracy suggestions
        if scores.get('brand_accuracy', 100) < 80:
            suggestions.append("Shorten headline to meet 7-word guideline")
            suggestions.append("Use approved CTA from brand whitelist")

        # Visual hierarchy suggestions
        if scores.get('visual_hierarchy', 100) < 70:
            suggestions.append("Increase headline font size for stronger hierarchy")
            suggestions.append("Add more contrast between headline and subhead")

        return suggestions

    def auto_improve_design(
        self,
        image: Image.Image,
        plan: DesignPlan,
        score: QualityScore
    ) -> Image.Image:
        """
        Automatically apply improvements based on quality score

        Args:
            image: Original design
            plan: Design plan
            score: Quality evaluation result

        Returns:
            Improved design image
        """
        logger.info("Applying automatic improvements...")

        improved = image.copy()

        # Apply fixes based on issues
        if any('text contrast' in issue.lower() for issue in score.issues):
            improved = self._enhance_text_contrast(improved)

        if any('cta' in issue.lower() for issue in score.issues):
            # Note: This requires knowing CTA position
            # For now, log that manual adjustment needed
            logger.info("CTA improvements require manual adjustment")

        return improved

    def _enhance_text_contrast(self, image: Image.Image) -> Image.Image:
        """Apply darker overlay to improve text contrast"""
        from PIL import ImageEnhance

        # Create a darker overlay on bottom third
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        width, height = image.size

        # Gradient overlay (darker at bottom)
        for y in range(int(height * 0.5), height):
            progress = (y - int(height * 0.5)) / (height * 0.5)
            alpha = int(progress * 150)  # 0-150 opacity
            draw.rectangle(
                [(0, y), (width, y + 1)],
                fill=(0, 0, 0, alpha)
            )

        # Composite
        image_rgba = image.convert('RGBA')
        improved = Image.alpha_composite(image_rgba, overlay)
        improved = improved.convert('RGB')

        logger.info("Enhanced text contrast with overlay")
        return improved


# Convenience function
def score_design_quality(
    image: Image.Image,
    plan: DesignPlan,
    tokens: BrandTokens,
    threshold: float = 70.0
) -> QualityScore:
    """
    Quick function to score a design

    Args:
        image: Rendered design
        plan: Design plan
        tokens: Brand tokens
        threshold: Quality threshold

    Returns:
        QualityScore
    """
    scorer = DesignQualityScorer(tokens, threshold)
    return scorer.score_design(image, plan)
