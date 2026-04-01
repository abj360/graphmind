#!/usr/bin/env python3
"""
entity_resolver.py --- entity resolution via normalized string matching (naive, pre-embedding)

Contains:
    normalize_name(): folds an entity name to its comparison key
    MergeDecision: one canonicalization applied to an entity
    ResolutionResult: resolved triples plus merge bookkeeping
    EntityResolver: canonicalizes entities via string matching
    EntityResolver.resolve(): canonicalizes all entity mentions
    EntityResolver._build_canonical_map(): exact-match canonical map
    EntityResolver._rewrite_triples(): applies the canonical map
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

    def resolve(self, triples: list[Triple]) -> ResolutionResult:
        """Canonicalizes duplicate entities across a set of triples.

        Args:
            triples: Raw triples that may contain duplicate entities.

        Returns:
            result: Resolved triples plus merge bookkeeping.
        """
        canonical_of = self._build_canonical_map(triples)
        resolved = self._rewrite_triples(triples, canonical_of)
        merges = [
            MergeDecision(canonical, alias, 1.0)
            for alias, canonical in sorted(canonical_of.items())
            if alias != canonical
        ]
        return ResolutionResult(triples=resolved, merges=merges)

    @staticmethod
    def _build_canonical_map(triples: list[Triple]) -> dict[str, str]:
        """Builds a canonical-name map using exact normalized matches only.

        Args:
            triples: Triples whose endpoints are scanned.

        Returns:
            mapping: Normalized name to first-seen surface form.
        """
        canonical_of: dict[str, str] = {}
        for triple in triples:
            for entity in (triple.subject, triple.object):
                key = normalize_name(entity.name)
                canonical_of.setdefault(key, key)
        return canonical_of

    @staticmethod
    def _rewrite_triples(triples: list[Triple], canonical_of: dict[str, str]) -> list[Triple]:
        """Rewrites triple endpoints to their canonical names.

        Args:
            triples: Original triples with unresolved entity names.
            canonical_of: Normalized name to canonical name mapping.

        Returns:
            resolved: Triples with canonicalized endpoints.
        """
        resolved: list[Triple] = []
        for triple in triples:
            subject_name = canonical_of.get(normalize_name(triple.subject.name), triple.subject.name)
            object_name = canonical_of.get(normalize_name(triple.object.name), triple.object.name)
            subject = triple.subject.model_copy(update={"name": subject_name})
            object_ = triple.object.model_copy(update={"name": object_name})
            resolved.append(triple.model_copy(update={"subject": subject, "object": object_}))
        return resolved
