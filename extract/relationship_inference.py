#!/usr/bin/env python3
"""
relationship_inference.py --- infers bridging relationships between disconnected subgraphs

Contains:
    InferenceConfig: knobs for the bridging pass
    BridgeCandidate: one proposed cross-component relationship
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
