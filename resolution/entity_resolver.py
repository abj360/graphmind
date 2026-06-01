#!/usr/bin/env python3
"""
entity_resolver.py --- embedding-based canonicalization of duplicate entities

Contains:
    MergeDecision: one canonicalization applied to an entity
    ResolutionResult: resolved triples plus merge bookkeeping
    EntityResolver: canonicalizes entities via embedding similarity
    EntityResolver.resolve(): canonicalizes all entity mentions
    EntityResolver._collect_entities(): distinct normalized names
    EntityResolver._cluster_entities(): union-find over similarities
    EntityResolver._find(): path-compressed root lookup
    EntityResolver._union(): merges two clusters
    EntityResolver._pick_representative(): chooses cluster canonical
    EntityResolver._rewrite_triples(): applies cluster mapping
    resolve_names(): canonicalizes a bare list of names
    summarize_merges(): renders merge decisions for review
    duplicate_rate(): measures entity duplication before resolution
    main(): CLI entrypoint for entity resolution
    module entrypoint guard
"""

from dataclasses import dataclass

from extract.schema import Triple
from resolution.embedding import EmbeddingProvider, NgramEmbeddingProvider, cosine_similarity


@dataclass(frozen=True)
class MergeDecision:
    """Records one entity merged into a canonical representative.

    Attributes:
        canonical: Representative name chosen for the cluster.
        alias: Duplicate name folded into the representative.
        similarity: Cosine similarity that justified the merge.
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
        borderline: Merge candidates below auto-merge but above review floor.
    """

    triples: list[Triple]
    merges: list[MergeDecision]
    borderline: list[MergeDecision]


class EntityResolver:
    """Canonicalizes duplicate entities using embedding cosine similarity.

    Attributes:
        provider: Embedding provider used to vectorize entity names.
        threshold: Similarity at or above which entities auto-merge.
        review_floor: Similarity above which borderline pairs are flagged
            for human review instead of being ignored.
    """

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        threshold: float = 0.85,
        review_floor: float = 0.7,
    ) -> None:
        """Creates a resolver with an injected embedding provider.

        Args:
            provider: Embedding backend; offline n-gram provider by default.
            threshold: Cosine similarity floor for automatic merges.
            review_floor: Cosine similarity floor for review candidates.
        """
        self.provider = provider or NgramEmbeddingProvider()
        self.threshold = threshold
        self.review_floor = review_floor

    def resolve(self, triples: list[Triple]) -> ResolutionResult:
        """Canonicalizes duplicate entities across a set of triples.

        Args:
            triples: Raw triples that may contain duplicate entities.

        Returns:
            result: Resolved triples plus merge and borderline bookkeeping.
        """
        names = self._collect_entities(triples)
        clusters, merges, borderline = self._cluster_entities(names)
        resolved = self._rewrite_triples(triples, clusters)
        return ResolutionResult(triples=resolved, merges=merges, borderline=borderline)

    @staticmethod
    def _collect_entities(triples: list[Triple]) -> list[str]:
        """Collects distinct normalized entity names from triples.

        Args:
            triples: Triples whose endpoints are scanned.

        Returns:
            names: Sorted distinct normalized entity names.
        """
        names: set[str] = set()
        for triple in triples:
            names.add(triple.subject.normalized_name())
            names.add(triple.object.normalized_name())
        return sorted(names)

    def _cluster_entities(
        self, names: list[str]
    ) -> tuple[dict[str, str], list[MergeDecision], list[MergeDecision]]:
        """Clusters entity names by embedding similarity via union-find.

        Args:
            names: Distinct normalized entity names to cluster.

        Returns:
            clusters: Mapping of each name to its cluster representative.
            merges: Auto-merge decisions applied.
            borderline: Pairs flagged for human review, not merged.
        """
        parent = {name: name for name in names}
        vectors = {name: self.provider.embed(name) for name in names}
        merges: list[MergeDecision] = []
        borderline: list[MergeDecision] = []
        for left_index, left in enumerate(names):
            for right in names[left_index + 1 :]:
                similarity = cosine_similarity(vectors[left], vectors[right])
                if similarity >= self.threshold:
                    self._union(parent, left, right)
                    merges.append(MergeDecision(self._find(parent, left), right, similarity))
                elif similarity >= self.review_floor:
                    borderline.append(MergeDecision(left, right, similarity))
        clusters = {name: self._pick_representative(parent, name) for name in names}
        return clusters, merges, borderline

    @classmethod
    def _find(cls, parent: dict[str, str], name: str) -> str:
        """Finds the cluster root of a name with path compression.

        Args:
            parent: Union-find parent mapping.
            name: Name whose root is looked up.

        Returns:
            root: Canonical root name of the cluster.
        """
        root = name
        while parent[root] != root:
            root = parent[root]
        while parent[name] != root:
            parent[name], name = root, parent[name]
        return root

    @classmethod
    def _union(cls, parent: dict[str, str], left: str, right: str) -> None:
        """Merges the clusters of two names, preferring the shorter root.

        Args:
            parent: Union-find parent mapping, mutated in place.
            left: First name whose cluster merges.
            right: Second name whose cluster merges.
        """
        left_root = cls._find(parent, left)
        right_root = cls._find(parent, right)
        if left_root == right_root:
            return
        canonical, alias = sorted((left_root, right_root), key=len)
        parent[alias] = canonical

    def _pick_representative(self, parent: dict[str, str], name: str) -> str:
        """Chooses the representative name for a name's cluster.

        Args:
            parent: Union-find parent mapping.
            name: Name whose cluster representative is chosen.

        Returns:
            representative: Root name of the cluster.
        """
        return self._find(parent, name)

    @staticmethod
    def _rewrite_triples(triples: list[Triple], clusters: dict[str, str]) -> list[Triple]:
        """Rewrites triple endpoints to their canonical cluster names.

        Args:
            triples: Original triples with unresolved entity names.
            clusters: Normalized name to canonical name mapping.

        Returns:
            resolved: Triples with canonicalized endpoints.
        """
        resolved: list[Triple] = []
        for triple in triples:
            subject_name = clusters.get(triple.subject.normalized_name(), triple.subject.name)
            object_name = clusters.get(triple.object.normalized_name(), triple.object.name)
            subject = triple.subject.model_copy(update={"name": subject_name})
            object_ = triple.object.model_copy(update={"name": object_name})
            resolved.append(triple.model_copy(update={"subject": subject, "object": object_}))
        return resolved


def resolve_names(names: list[str], threshold: float = 0.85) -> dict[str, str]:
    """Canonicalizes a bare list of entity names without triples.

    Args:
        names: Entity names to cluster and canonicalize.
        threshold: Cosine similarity floor for automatic merges.

    Returns:
        mapping: Normalized name to canonical representative name.
    """
    resolver = EntityResolver(threshold=threshold)
    normalized_of = {name: " ".join(name.casefold().split()) for name in names}
    distinct = sorted(set(normalized_of.values()))
    parent = {name: name for name in distinct}
    vectors = {name: resolver.provider.embed(name) for name in distinct}
    for left_index, left in enumerate(distinct):
        for right in distinct[left_index + 1 :]:
            if cosine_similarity(vectors[left], vectors[right]) >= threshold:
                resolver._union(parent, left, right)
    return {name: resolver._find(parent, normalized_of[name]) for name in names}


def summarize_merges(result: ResolutionResult) -> str:
    """Renders merge decisions as a human-readable summary.

    Args:
        result: Resolution output containing merge bookkeeping.

    Returns:
        summary: Newline-joined merge and borderline descriptions.
    """
    lines = [f"MERGE {m.alias} -> {m.canonical} (sim={m.similarity:.3f})" for m in result.merges]
    lines.extend(
        f"REVIEW {m.alias} ~ {m.canonical} (sim={m.similarity:.3f})" for m in result.borderline
    )
    return "\n".join(lines)


def duplicate_rate(triples: list[Triple]) -> float:
    """Measures how inflated the entity count is before resolution.

    Args:
        triples: Triples whose entity duplication is measured.

    Returns:
        rate: Share of mentions that are duplicates of another mention.
    """
    mentions: list[str] = []
    for triple in triples:
        mentions.append(triple.subject.normalized_name())
        mentions.append(triple.object.normalized_name())
    if not mentions:
        return 0.0
    return 1.0 - len(set(mentions)) / len(mentions)


def main(argv: list[str] | None = None) -> int:
    """Runs the resolution CLI over an extracted-triples JSONL file.

    Args:
        argv: Command-line arguments; sys.argv when omitted.

    Returns:
        exit_code: 0 on success, nonzero on failure.
    """
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Resolve duplicate entities in a triple graph")
    parser.add_argument("--graph", required=True, help="extracted triples JSONL path")
    parser.add_argument("--out", default="out/resolved.jsonl", help="output JSONL path")
    parser.add_argument("--threshold", type=float, default=0.85, help="auto-merge threshold")
    args = parser.parse_args(argv)
    triples = [
        Triple.model_validate(json.loads(line))
        for line in Path(args.graph).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result = EntityResolver(threshold=args.threshold).resolve(triples)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for triple in result.triples:
            handle.write(json.dumps(triple.model_dump()) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
