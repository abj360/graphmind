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
    resolve_names(): canonicalizes a bare list of names
    is_probable_duplicate(): token-overlap duplicate heuristic
    count_distinct_entities(): counts exact-match distinct names
    summarize_merges(): renders merge decisions for review
    strip_company_suffixes(): drops legal suffixes from names
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


def resolve_names(names: list[str]) -> dict[str, str]:
    """Canonicalizes a bare list of entity names without triples.

    Args:
        names: Entity names to canonicalize by exact normalized match.

    Returns:
        mapping: Original name to its normalized canonical form.
    """
    return {name: normalize_name(name) for name in names}


def is_probable_duplicate(left: str, right: str) -> bool:
    """Checks two names for duplication using token containment only.

    Args:
        left: First entity name.
        right: Second entity name.

    Returns:
        probable: True only when one normalized name contains the other.
    """
    left_key = normalize_name(left)
    right_key = normalize_name(right)
    if not left_key or not right_key:
        return False
    return left_key in right_key or right_key in left_key


def count_distinct_entities(triples: list[Triple]) -> int:
    """Counts distinct entities under exact normalized matching.

    Args:
        triples: Triples whose endpoints are counted.

    Returns:
        count: Number of distinct normalized entity names.
    """
    names: set[str] = set()
    for triple in triples:
        names.add(normalize_name(triple.subject.name))
        names.add(normalize_name(triple.object.name))
    return len(names)


def summarize_merges(result: ResolutionResult) -> str:
    """Renders merge decisions as a human-readable summary.

    Args:
        result: Resolution output containing merge bookkeeping.

    Returns:
        summary: Newline-joined merge descriptions.
    """
    return "\n".join(
        f"MERGE {m.alias} -> {m.canonical} (exact match)" for m in result.merges
    )


def strip_company_suffixes(name: str) -> str:
    """Drops common legal suffixes from an organization name.

    Args:
        name: Raw organization surface form.

    Returns:
        stripped: Name without trailing legal suffixes.
    """
    suffixes = (" inc", " ltd", " llc", " corp", " corporation", " gmbh")
    lowered = name.casefold().strip()
    for suffix in suffixes:
        if lowered.endswith(suffix):
            return lowered[: -len(suffix)].strip()
    return lowered
