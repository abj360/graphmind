#!/usr/bin/env python3
"""
relationship_inference.py --- infers bridging relationships between disconnected subgraphs

Contains:
    InferenceConfig: knobs for the bridging pass
    BridgeCandidate: one proposed cross-component relationship
    RelationshipInferer: finds and bridges disconnected subgraphs
    RelationshipInferer._build_adjacency(): entity to neighbor map
    RelationshipInferer._connected_components(): groups entities
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
