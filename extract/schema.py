#!/usr/bin/env python3
"""
schema.py --- pydantic models and validation helpers for extracted SPO triples

Contains:
    SourceSpan: character offsets anchoring a triple to its source text
    SourceSpan.end_after_start(): rejects zero-length or inverted spans
    EntityRef: one endpoint of an SPO triple
    EntityRef.normalized_name(): case-folded comparison key
    Triple: one validated subject-predicate-object fact
    Triple.key(): deduplication identity tuple
    clamp_confidence(): clamps a score into the unit interval
    ConfidenceStats: summary statistics over triple confidence
    validate_triple(): coerces one raw dict into a Triple
    confidence_stats(): computes ConfidenceStats for a batch
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceSpan(BaseModel):
    """Locates the exact passage a triple was extracted from.

    Attributes:
        start: Inclusive character offset of the cited passage.
        end: Exclusive character offset of the cited passage.
        text: Verbatim cited passage from the source document.
    """

    model_config = ConfigDict(frozen=True)

    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)

    @field_validator("end")
    @classmethod
    def end_after_start(cls, value: int, info: Any) -> int:
        """Validates that the span end is strictly greater than its start.

        Args:
            value: Candidate end offset.
            info: Pydantic validation context carrying sibling field values.

        Returns:
            value: The accepted end offset.
        """
        start = info.data.get("start")
        if start is not None and value <= start:
            msg = f"span end {value} must be greater than start {start}"
            raise ValueError(msg)
        return value


class EntityRef(BaseModel):
    """Represents a named entity participating in a triple.

    Attributes:
        name: Surface form of the entity as seen in the source text.
        entity_type: Coarse type label such as PERSON, ORG, or CONCEPT.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    entity_type: str = Field(default="CONCEPT", min_length=1)

    @field_validator("name", "entity_type")
    @classmethod
    def strip_and_check(cls, value: str) -> str:
        """Normalizes whitespace and rejects blank values.

        Args:
            value: Raw field value supplied by the extractor.

        Returns:
            value: Trimmed, non-empty field value.
        """
        cleaned = value.strip()
        if not cleaned:
            msg = "entity fields must not be blank"
            raise ValueError(msg)
        return cleaned

    def normalized_name(self) -> str:
        """Computes the case-folded comparison key for this entity.

        Returns:
            key: Lowercased, whitespace-collapsed entity name.
        """
        return " ".join(self.name.casefold().split())


class Triple(BaseModel):
    """Represents a single extracted fact with provenance and confidence.

    Attributes:
        subject: Entity the fact is about.
        predicate: Relationship phrase linking subject and object.
        object: Entity the subject is related to.
        confidence: Extractor confidence in the fact, between 0 and 1.
        source_doc_id: Identifier of the document the fact came from.
        source_span: Cited passage supporting the fact, when required.
        inferred: Whether the triple was inferred rather than extracted.
    """

    model_config = ConfigDict(frozen=True)

    subject: EntityRef
    predicate: str = Field(min_length=1)
    object: EntityRef
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_doc_id: str = Field(min_length=1)
    source_span: SourceSpan | None = None
    inferred: bool = False

    @field_validator("predicate")
    @classmethod
    def normalize_predicate(cls, value: str) -> str:
        """Normalizes predicate phrasing to a stable comparable form.

        Args:
            value: Raw predicate phrase from the extractor.

        Returns:
            value: Trimmed predicate with internal whitespace collapsed.
        """
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            msg = "predicate must not be blank"
            raise ValueError(msg)
        return cleaned

    def key(self) -> tuple[str, str, str]:
        """Computes the deduplication key for this triple.

        Returns:
            key: Normalized (subject, predicate, object) identity tuple.
        """
        return (
            self.subject.normalized_name(),
            self.predicate.casefold(),
            self.object.normalized_name(),
        )


def clamp_confidence(score: float) -> float:
    """Clamps an arbitrary numeric score into [0.0, 1.0].

    Args:
        score: Raw confidence value, possibly out of range.

    Returns:
        clamped: Score constrained to the valid confidence interval.
    """
    return max(0.0, min(1.0, score))


class ConfidenceStats(BaseModel):
    """Summarizes the confidence distribution of a triple batch.

    Attributes:
        count: Number of triples the statistics were computed over.
        mean: Average confidence across the batch.
        low_confidence_count: Number of triples below the review threshold.
    """

    model_config = ConfigDict(frozen=True)

    count: int = Field(ge=0)
    mean: float = Field(ge=0.0, le=1.0)
    low_confidence_count: int = Field(ge=0)


def validate_triple(raw: dict[str, Any], source_doc_id: str) -> Triple:
    """Coerces one raw extractor payload into a validated Triple.

    Args:
        raw: Unvalidated mapping produced by the LLM response parser.
        source_doc_id: Document identifier stamped onto the triple.

    Returns:
        triple: Validated, immutable Triple instance.
    """
    payload = {**raw, "source_doc_id": source_doc_id}
    return Triple.model_validate(payload)


def confidence_stats(triples: list[Triple], review_threshold: float = 0.6) -> ConfidenceStats:
    """Computes summary confidence statistics for a batch of triples.

    Args:
        triples: Triples whose confidence distribution is summarized.
        review_threshold: Score below which a triple counts as low-confidence.

    Returns:
        stats: Aggregated count, mean, and low-confidence tally.
    """
    if not triples:
        return ConfidenceStats(count=0, mean=0.0, low_confidence_count=0)
    mean = sum(t.confidence for t in triples) / len(triples)
    low = sum(1 for t in triples if t.confidence < review_threshold)
    return ConfidenceStats(count=len(triples), mean=mean, low_confidence_count=low)
