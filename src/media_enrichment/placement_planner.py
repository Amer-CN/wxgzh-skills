"""Placement planner module.

Suggests image placement positions in the article based on claim_id
and section anchors. Does NOT directly modify article text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PlacementSuggestion:
    """Suggestion for image placement."""
    anchor: str
    position: str  # "before" or "after"
    confidence: float
    caption: str
    alt_text: str
    review_required: bool = False


def find_anchors(article_path: str | Path, claim_texts: list[str]) -> dict[str, PlacementSuggestion]:
    """Find placement anchors for claims in the article.

    Args:
        article_path: Path to the article markdown file.
        claim_texts: List of claim texts to find anchors for.

    Returns:
        Dict mapping claim_text -> PlacementSuggestion.
    """
    result: dict[str, PlacementSuggestion] = {}

    try:
        content = Path(article_path).read_text(encoding="utf-8")
    except Exception:
        for ct in claim_texts:
            result[ct] = PlacementSuggestion(
                anchor="", position="after", confidence=0.0,
                caption="", alt_text="", review_required=True,
            )
        return result

    lines = content.split("\n")

    # Find heading positions for context
    heading_indices = []
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            heading_indices.append((i, line.strip()))

    for claim_text in claim_texts:
        # Try to find the claim text in the article
        found = False
        for i, line in enumerate(lines):
            if claim_text[:30] in line:
                # Found — suggest placement after this line
                anchor = line.strip()[:80]
                result[claim_text] = PlacementSuggestion(
                    anchor=anchor,
                    position="after",
                    confidence=0.9,
                    caption=f"图：{claim_text[:40]}",
                    alt_text=claim_text[:60],
                    review_required=False,
                )
                found = True
                break

        if not found:
            # Try to find a nearby heading
            for heading_idx, heading_text in heading_indices:
                # Check if any words from claim appear in heading
                words = claim_text.split()
                if any(w in heading_text for w in words if len(w) > 2):
                    result[claim_text] = PlacementSuggestion(
                        anchor=heading_text[:80],
                        position="after",
                        confidence=0.5,
                        caption=f"图：{claim_text[:40]}",
                        alt_text=claim_text[:60],
                        review_required=True,
                    )
                    found = True
                    break

        if not found:
            result[claim_text] = PlacementSuggestion(
                anchor="", position="after", confidence=0.0,
                caption=f"图：{claim_text[:40]}",
                alt_text=claim_text[:60],
                review_required=True,
            )

    return result
