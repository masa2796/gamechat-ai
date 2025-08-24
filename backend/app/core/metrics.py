"""Prometheus metrics (stub) for feedback & search instrumentation.

This module isolates counter declarations to avoid circular imports.
Counters are automatically registered in the default Prometheus registry
when this module is imported anywhere in the app lifecycle.

Metrics:
  - gamechat_ai_feedback_total{rating,query_type}
  - gamechat_ai_zero_hit_total

Label semantics:
  rating: str  ("-1", "0", "1")  // numeric rating as string
  query_type: str (semantic|hybrid|filterable|greeting|unknown)

These are intentionally minimal (雛形). Histograms / more labels can be added later.
"""
from __future__ import annotations

from prometheus_client import Counter
from typing import Optional

# Feedback submissions counter
FEEDBACK_COUNTER = Counter(
    "gamechat_ai_feedback_total",
    "Total number of feedback submissions received",
    ["rating", "query_type"],
)

# Zero-hit (no search results) counter
ZERO_HIT_COUNTER = Counter(
    "gamechat_ai_zero_hit_total",
    "Total number of search queries resulting in zero hits",
)

def inc_feedback(rating: int, query_type: Optional[str]) -> None:
    """Increment feedback counter.

    rating: -1 / 0 / 1 (converted to string label)
    query_type: may be None -> 'unknown'
    """
    try:
        FEEDBACK_COUNTER.labels(rating=str(rating), query_type=(query_type or "unknown")).inc()
    except Exception:
        # Silently ignore metric errors (stub resilience)
        pass

def inc_zero_hit() -> None:
    """Increment zero-hit counter."""
    try:
        ZERO_HIT_COUNTER.inc()
    except Exception:
        pass
