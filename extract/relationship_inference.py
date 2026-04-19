#!/usr/bin/env python3
"""
relationship_inference.py --- infers bridging relationships between disconnected subgraphs

Contains:
    InferenceConfig: knobs for the bridging pass
    BridgeCandidate: one proposed cross-component relationship
    RelationshipInferer: finds and bridges disconnected subgraphs
    RelationshipInferer._build_adjacency(): entity to neighbor map
    RelationshipInferer._connected_components(): groups entities
    RelationshipInferer.infer(): proposes and materializes bridges
    RelationshipInferer._candidate_bridges(): scores component pairs
    RelationshipInferer._entity_types(): entity name to type map
    RelationshipInferer._score_bridge(): heuristic bridge scoring
    RelationshipInferer._share_tokens(): cheap name-overlap signal
"""

from dataclasses import dataclass

from extract.schema import Triple


@dataclass(frozen=True)
class InferenceConfig:
    """Controls how aggressively bridges between subgraphs are inferred.

    Attributes:
        min_bridge_confidence: Minimum score for an inferred bridge to ship.
        candidate_limit: Maximum candidate pairs considered per component pair.
        max_components: Components beyond this count are skipped for safety.
    """

    min_bridge_confidence: float = 0.55
    candidate_limit: int = 25
    max_components: int = 50


@dataclass(frozen=True)
class BridgeCandidate:
    """Represents a proposed relationship bridging two components.

    Attributes:
        source_name: Canonical entity name in the first component.
        target_name: Canonical entity name in the second component.
        predicate: Proposed predicate phrase for the bridge.
        score: Confidence score assigned by the bridging heuristic.
    """

    source_name: str
    target_name: str
    predicate: str
    score: float


class RelationshipInferer:
    """Infers bridging relationships that connect disconnected subgraphs.

    Attributes:
        config: Inference tunables controlling bridge selection.
    """

    def __init__(self, config: InferenceConfig | None = None) -> None:
        """Creates an inferer with the given bridging configuration.

        Args:
            config: Inference overrides; defaults applied when omitted.
        """
        self.config = config or InferenceConfig()

    @staticmethod
    def _build_adjacency(triples: list[Triple]) -> dict[str, set[str]]:
        """Builds an undirected adjacency map over entity names.

        Args:
            triples: Triples whose endpoints become graph edges.

        Returns:
            adjacency: Mapping of entity name to connected entity names.
        """
        adjacency: dict[str, set[str]] = {}
        for triple in triples:
            subject = triple.subject.normalized_name()
            object_ = triple.object.normalized_name()
            adjacency.setdefault(subject, set()).add(object_)
            adjacency.setdefault(object_, set()).add(subject)
        return adjacency

    def _connected_components(self, triples: list[Triple]) -> list[set[str]]:
        """Groups entity names into connected components.

        Args:
            triples: Triples defining the graph to partition.

        Returns:
            components: Disjoint sets of connected entity names.
        """
        adjacency = self._build_adjacency(triples)
        seen: set[str] = set()
        components: list[set[str]] = []
        for start in adjacency:
            if start in seen:
                continue
            stack = [start]
            component: set[str] = set()
            while stack:
                node = stack.pop()
                if node in seen:
                    continue
                seen.add(node)
                component.add(node)
                stack.extend(adjacency[node] - seen)
            components.append(component)
        return components

    def infer(self, triples: list[Triple]) -> list[Triple]:
        """Infers bridging triples connecting disconnected components.

        Args:
            triples: Extracted triples forming possibly disjoint subgraphs.

        Returns:
            bridges: Inferred triples marked with inferred=True.
        """
        components = self._connected_components(triples)
        if len(components) < 2 or len(components) > self.config.max_components:
            return []
        bridges: list[Triple] = []
        for left_index in range(len(components)):
            for right_index in range(left_index + 1, len(components)):
                candidates = self._candidate_bridges(
                    triples, components[left_index], components[right_index]
                )
                bridges.extend(self._materialize(candidates))
        return bridges

    def _candidate_bridges(
        self, triples: list[Triple], left: set[str], right: set[str]
    ) -> list[BridgeCandidate]:
        """Scores candidate bridges between two disconnected components.

        Args:
            triples: Full triple set providing type context.
            left: Entity names of the first component.
            right: Entity names of the second component.

        Returns:
            candidates: Scored bridge candidates above the confidence floor.
        """
        types = self._entity_types(triples)
        candidates: list[BridgeCandidate] = []
        for source in sorted(left):
            for target in sorted(right):
                score, predicate = self._score_bridge(source, target, types)
                if score >= self.config.min_bridge_confidence:
                    candidates.append(BridgeCandidate(source, target, predicate, score))
        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        return candidates[: self.config.candidate_limit]

    @staticmethod
    def _entity_types(triples: list[Triple]) -> dict[str, str]:
        """Maps normalized entity names to their entity types.

        Args:
            triples: Triples supplying entity type information.

        Returns:
            types: Mapping of normalized entity name to entity type.
        """
        types: dict[str, str] = {}
        for triple in triples:
            types[triple.subject.normalized_name()] = triple.subject.entity_type
            types[triple.object.normalized_name()] = triple.object.entity_type
        return types

    def _score_bridge(self, source: str, target: str, types: dict[str, str]) -> tuple[float, str]:
        """Scores a potential bridge between two entities.

        Args:
            source: Normalized name of the bridge source entity.
            target: Normalized name of the bridge target entity.
            types: Entity name to type mapping for context.

        Returns:
            score: Confidence score between 0 and 1.
            predicate: Suggested predicate phrase for the bridge.
        """
        source_type = types.get(source, "CONCEPT")
        target_type = types.get(target, "CONCEPT")
        score = 0.4
        predicate = "relates to"
        if source_type == target_type:
            score += 0.15
            predicate = "associated with"
        if source_type == "PERSON" and target_type == "ORG":
            score += 0.2
            predicate = "affiliated with"
        if source_type == "ORG" and target_type == "ORG":
            score += 0.1
            predicate = "related to"
        if self._share_tokens(source, target):
            score += 0.1
        return min(score, 0.95), predicate

    @staticmethod
    def _share_tokens(source: str, target: str) -> bool:
        """Checks whether two entity names share a significant token.

        Args:
            source: First normalized entity name.
            target: Second normalized entity name.

        Returns:
            shares: True when the names share a token of length four or more.
        """
        source_tokens = {token for token in source.split() if len(token) >= 4}
        target_tokens = {token for token in target.split() if len(token) >= 4}
        return bool(source_tokens & target_tokens)
