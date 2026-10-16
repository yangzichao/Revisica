"""Turning free-form LLM output into structured data shared by every lane."""

from .json_object_extraction import extract_json_object

__all__ = ["extract_json_object"]
