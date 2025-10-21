"""
Canva Template Validator
Inspects brand templates for autofill compatibility
Validates placeholder configuration and provides diagnostics
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import requests

from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TemplateValidationResult:
    """Template validation result"""
    template_id: str
    is_valid: bool
    has_autofill_fields: bool
    placeholder_fields: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "template_id": self.template_id,
            "is_valid": self.is_valid,
            "has_autofill_fields": self.has_autofill_fields,
            "placeholder_fields": self.placeholder_fields,
            "issues": self.issues,
            "warnings": self.warnings,
            "metadata": self.metadata
        }


class CanvaTemplateValidator:
    """
    Validates Canva brand templates for autofill compatibility

    Checks:
    - Template exists and is accessible
    - Has autofill-capable data fields
    - Placeholder names match expectations
    - Field types are correct (text, image)
    """

    def __init__(self, access_token: str):
        """
        Initialize validator

        Args:
            access_token: Canva API access token
        """
        self.access_token = access_token
        self.api_base = settings.CANVA_API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })

        # Expected placeholder names for validation
        self.expected_placeholders = {
            "HEADLINE": "text",
            "SUBHEAD": "text",
            "CTA_TEXT": "text",
            "MAIN_IMAGE": "image",
            "PRODUCT_IMAGE": "image"  # Optional
        }

    def inspect_template(self, template_id: str) -> TemplateValidationResult:
        """
        Inspect brand template and validate configuration

        Args:
            template_id: Canva brand template ID

        Returns:
            TemplateValidationResult with detailed diagnostics
        """
        logger.info(f"Inspecting template: {template_id}")

        issues = []
        warnings = []
        placeholder_fields = []
        metadata = {}

        try:
            # Step 1: Get template metadata
            template_info = self._get_template_info(template_id)

            if not template_info:
                return TemplateValidationResult(
                    template_id=template_id,
                    is_valid=False,
                    has_autofill_fields=False,
                    issues=["Template not found or not accessible"]
                )

            metadata["name"] = template_info.get("name", "Unknown")
            metadata["dimensions"] = {
                "width": template_info.get("width", {}).get("value"),
                "height": template_info.get("height", {}).get("value")
            }

            # Step 2: Get template dataset (autofill fields)
            dataset = self._get_template_dataset(template_id)

            if not dataset:
                issues.append("Template does not have autofill-capable data fields")
                return TemplateValidationResult(
                    template_id=template_id,
                    is_valid=False,
                    has_autofill_fields=False,
                    issues=issues,
                    metadata=metadata
                )

            # Step 3: Analyze data fields
            fields = dataset.get("fields", [])

            if not fields:
                issues.append("No data fields found in template dataset")
                return TemplateValidationResult(
                    template_id=template_id,
                    is_valid=False,
                    has_autofill_fields=False,
                    issues=issues,
                    metadata=metadata
                )

            # Extract field information
            for field in fields:
                field_name = field.get("name")
                field_type = field.get("type")

                if field_name:
                    placeholder_fields.append(field_name)

                    # Validate field configuration
                    if field_name in self.expected_placeholders:
                        expected_type = self.expected_placeholders[field_name]

                        if field_type != expected_type:
                            issues.append(
                                f"Field '{field_name}' has type '{field_type}' but expected '{expected_type}'"
                            )
                    else:
                        warnings.append(f"Unknown field '{field_name}' (not in standard set)")

            # Step 4: Check for required fields
            required_fields = ["HEADLINE", "SUBHEAD", "CTA_TEXT", "MAIN_IMAGE"]
            missing_fields = [f for f in required_fields if f not in placeholder_fields]

            if missing_fields:
                issues.append(f"Missing required fields: {', '.join(missing_fields)}")

            # Determine if valid
            is_valid = len(issues) == 0
            has_autofill = len(placeholder_fields) > 0

            result = TemplateValidationResult(
                template_id=template_id,
                is_valid=is_valid,
                has_autofill_fields=has_autofill,
                placeholder_fields=placeholder_fields,
                issues=issues,
                warnings=warnings,
                metadata=metadata
            )

            logger.info(f"Template validation: {'PASS' if is_valid else 'FAIL'}")
            return result

        except Exception as e:
            logger.error(f"Template inspection failed: {e}")
            return TemplateValidationResult(
                template_id=template_id,
                is_valid=False,
                has_autofill_fields=False,
                issues=[f"Inspection error: {str(e)}"]
            )

    def _get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get basic template information"""
        try:
            # Note: Canva API doesn't have a direct endpoint to get single template
            # We need to list all templates and find this one
            url = f"{self.api_base}/brand-templates"
            params = {"limit": 100}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            templates = data.get("items", [])

            # Find our template
            for template in templates:
                if template.get("id") == template_id:
                    return template

            logger.warning(f"Template {template_id} not found in list")
            return None

        except Exception as e:
            logger.error(f"Failed to get template info: {e}")
            return None

    def _get_template_dataset(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template dataset (autofill fields)"""
        try:
            url = f"{self.api_base}/brand-templates/{template_id}/dataset"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Retrieved dataset with {len(data.get('fields', []))} fields")
            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning("Template dataset not found - template may not have data fields")
            else:
                logger.error(f"Failed to get template dataset: {e}")
            return None
        except Exception as e:
            logger.error(f"Dataset retrieval error: {e}")
            return None

    def batch_validate_templates(
        self,
        template_ids: List[str]
    ) -> Dict[str, TemplateValidationResult]:
        """
        Validate multiple templates

        Args:
            template_ids: List of template IDs to validate

        Returns:
            Dict mapping template_id to validation result
        """
        results = {}

        for template_id in template_ids:
            result = self.inspect_template(template_id)
            results[template_id] = result

        return results

    def suggest_fixes(self, result: TemplateValidationResult) -> List[str]:
        """
        Suggest fixes for template issues

        Args:
            result: Validation result

        Returns:
            List of actionable suggestions
        """
        suggestions = []

        if not result.has_autofill_fields:
            suggestions.append(
                "This template doesn't have data fields. "
                "In Canva template editor:\n"
                "1. Select each text/image element\n"
                "2. Convert to 'Data field'\n"
                "3. Name them: HEADLINE, SUBHEAD, CTA_TEXT, MAIN_IMAGE"
            )

        for issue in result.issues:
            if "Missing required fields" in issue:
                suggestions.append(
                    "Add missing data fields in Canva template editor. "
                    "Required: HEADLINE (text), SUBHEAD (text), CTA_TEXT (text), MAIN_IMAGE (image)"
                )

            if "type" in issue.lower() and "expected" in issue.lower():
                suggestions.append(
                    "Fix field type mismatch. Ensure text fields are 'Text' type "
                    "and image fields are 'Image' type in Canva."
                )

        if not result.is_valid and not suggestions:
            suggestions.append(
                "Review template configuration in Canva and ensure all data fields are properly configured."
            )

        return suggestions


# Convenience function
def validate_template(template_id: str, access_token: str) -> TemplateValidationResult:
    """
    Quick function to validate a template

    Args:
        template_id: Canva brand template ID
        access_token: Canva API access token

    Returns:
        TemplateValidationResult
    """
    validator = CanvaTemplateValidator(access_token)
    return validator.inspect_template(template_id)
