#!/usr/bin/env python3
"""
entity_resolver.py --- entity resolution via normalized string matching (naive, pre-embedding)

Contains:
    normalize_name(): folds an entity name to its comparison key
    MergeDecision: one canonicalization applied to an entity
    ResolutionResult: resolved triples plus merge bookkeeping
    EntityResolver: canonicalizes entities via string matching
"""

import re
from dataclasses import dataclass

from extract.schema import Triple


def normalize_name(name: str) -> str:
    """Folds an entity name into a normalized comparison key.

    Args:
        name: Raw entity surface form.

    Returns:
        key: Lowercased, punctuation-stripped, whitespace-collapsed name.
    """
    stripped = re.sub(r"[^\w\s]", "", name)
    return " ".join(stripped.casefold().split())


@dataclass(frozen=True)
class MergeDecision:
    """Records one entity merged into a canonical representative.

    Attributes:
        canonical: Representative name chosen for the cluster.
        alias: Duplicate name folded into the representative.
        similarity: Match score that justified the merge.
    """

    canonical: str
    alias: str
    similarity: float


@dataclass(frozen=True)
class ResolutionResult:
    """Bundles resolved triples with the decisions that produced them.

    Attributes:
        triples: Triples rewritten to canonical entity names.
        merges: Merge decisions applied during resolution.
    """

    triples: list[Triple]
    merges: list[MergeDecision]


class EntityResolver:
    """Canonicalizes duplicate entities by normalized string equality.

    Attributes:
        threshold: Unused placeholder kept for interface compatibility.
    """

    def __init__(self, threshold: float = 0.85) -> None:
        """Creates a naive string-matching resolver.

        Args:
            threshold: Retained for interface compatibility only.
        """
        self.threshold = threshold
