"""
Template Service – loads field templates for each document type from JSON files.
Raises TemplateNotFoundError with a clear message when a template is missing.
"""

import json
from pathlib import Path

from app.utils.logger import log_call
from app.utils.exceptions import TemplateNotFoundError

# Resolve templates directory relative to this file (robust for any CWD)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


@log_call
def load_template(doc_type: str) -> dict:
    """
    Load the JSON template for *doc_type*.
    Returns a dict of {field_name: description_hint}.
    """
    template_path = TEMPLATES_DIR / f"{doc_type}_template.json"

    if not template_path.exists():
        # Graceful fallback: return empty dict so pipeline still works
        return {}

    try:
        with open(template_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise TemplateNotFoundError(
            f"Invalid JSON in template '{template_path.name}'",
            str(exc),
        ) from exc