"""
JSON serialization utilities
"""
import math
from typing import Any, Dict, List


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize an object to be JSON-compliant.
    Replaces NaN, Inf, and -Inf with None.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Convert value to float, returning default if NaN or Inf.
    """
    try:
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (ValueError, TypeError):
        return default
