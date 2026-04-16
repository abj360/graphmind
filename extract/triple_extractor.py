#!/usr/bin/env python3
"""
triple_extractor.py --- LLM-based extraction of SPO triples from text chunks

Contains:
    DEFAULT_MODEL: fallback model identifier
    ExtractionConfig: tunables for the extraction pass
    ExtractionStats: running counters for an extraction pass
    ExtractionError: unrecoverable extraction failure
    TripleExtractor: turns text into validated triples via an LLM
    TripleExtractor._build_prompt(): renders the extraction prompt
    TripleExtractor._complete_with_retry(): retries transient failures
    TripleExtractor._parse_response(): parses raw JSON into triples
    TripleExtractor._extract_json_array(): pulls the JSON array out
    TripleExtractor._coerce_item(): validates one raw triple dict
    TripleExtractor.extract_text(): extracts triples from one document
    TripleExtractor.describe_config(): human-readable config summary
    TripleExtractor.extract_batch(): extracts from many texts at once
    TripleExtractor._batch_documents(): groups documents under batch size
    TripleExtractor._render_batch_prompt(): joins chunks into one prompt
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from extract.llm_client import LLMClient
from extract.prompts.config import PromptConfig, load_prompt_config
from extract.prompts.templates import build_extraction_prompt
from extract.schema import Triple, clamp_confidence, validate_triple

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class ExtractionConfig:
    """Controls model choice, retries, batching, and confidence handling.

    Attributes:
        model: Provider model identifier used for completions.
        max_retries: Attempts per prompt before giving up.
        request_timeout_seconds: Per-call timeout budget.
        batch_size: Maximum chunks sent per batched request.
        batch_token_budget: Approximate token ceiling per batched prompt.
        min_confidence: Triples scoring below this are dropped.
    """

    model: str = DEFAULT_MODEL
    max_retries: int = 2
    request_timeout_seconds: float = 30.0
    batch_size: int = 8
    batch_token_budget: int = 6_000
    min_confidence: float = 0.0


@dataclass
class ExtractionStats:
    """Tracks counters describing one extraction run.

    Attributes:
        calls_made: Number of LLM completions requested.
        triples_extracted: Number of triples kept after all filtering.
        retries: Number of retry attempts after transient failures.
        dropped_low_confidence: Triples discarded by the confidence floor.
    """

    calls_made: int = 0
    triples_extracted: int = 0
    retries: int = 0
    dropped_low_confidence: int = 0


class ExtractionError(RuntimeError):
    """Raised when extraction cannot proceed despite retries."""


class TripleExtractor:
    """Extracts validated SPO triples from text using an LLM client.

    Attributes:
        client: Completion provider used for extraction prompts.
        config: Extraction tunables (model, retries, confidence).
        prompt_config: Decoupled prompt rendering configuration.
        stats: Mutable counters for the current or last run.
    """

    def __init__(
        self,
        client: LLMClient,
        config: ExtractionConfig | None = None,
        prompt_config: PromptConfig | None = None,
    ) -> None:
        """Creates an extractor with injected dependencies.

        Args:
            client: Completion provider; tests pass a scripted fake.
            config: Extraction tunables; defaults applied when omitted.
            prompt_config: Prompt rendering config; loaded when omitted.
        """
        self.client = client
        self.config = config or ExtractionConfig()
        self.prompt_config = prompt_config or load_prompt_config()
        self.stats = ExtractionStats()

    def _build_prompt(self, text: str) -> str:
        """Renders the extraction prompt for one text window.

        Args:
            text: Text window the model should extract triples from.

        Returns:
            prompt: Fully rendered prompt string.
        """
        return build_extraction_prompt(text, self.prompt_config)

    def _complete_with_retry(self, prompt: str) -> str:
        """Requests a completion, retrying transient failures with backoff.

        Args:
            prompt: Rendered prompt to complete.

        Returns:
            completion: Raw model output from the first successful attempt.
        """
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                self.stats.calls_made += 1
                return self.client.complete(prompt)
            except RuntimeError as exc:
                last_error = exc
                self.stats.retries += 1
                logger.warning("LLM call failed (attempt %d): %s", attempt + 1, exc)
        raise ExtractionError(f"LLM completion failed after retries: {last_error}")

    def _parse_response(self, raw: str, doc_id: str) -> list[Triple]:
        """Parses one raw completion into validated, filtered triples.

        Args:
            raw: Raw model output expected to embed a JSON array.
            doc_id: Document identifier stamped onto produced triples.

        Returns:
            triples: Validated triples passing the confidence floor.
        """
        items = self._extract_json_array(raw)
        triples: list[Triple] = []
        for item in items:
            triple = self._coerce_item(item, doc_id)
            if triple is None:
                continue
            if triple.confidence < self.config.min_confidence:
                self.stats.dropped_low_confidence += 1
                continue
            triples.append(triple)
        return triples

    @staticmethod
    def _extract_json_array(raw: str) -> list[dict[str, Any]]:
        """Extracts the first JSON array embedded in raw model output.

        Args:
            raw: Model output, possibly wrapped in prose or code fences.

        Returns:
            items: Parsed objects from the embedded JSON array.
        """
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            logger.warning("no JSON array found in LLM response")
            return []
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.warning("malformed JSON array in LLM response")
            return []
        if not isinstance(parsed, list):
            return []
        return [item for item in parsed if isinstance(item, dict)]

    @staticmethod
    def _coerce_item(item: dict[str, Any], doc_id: str) -> Triple | None:
        """Validates one raw payload into a Triple, or None on failure.

        Args:
            item: Raw mapping from the parsed JSON array.
            doc_id: Document identifier stamped onto the triple.

        Returns:
            triple: Validated triple, or None when validation fails.
        """
        try:
            if "confidence" in item:
                item = {**item, "confidence": clamp_confidence(float(item["confidence"]))}
            return validate_triple(item, doc_id)
        except (ValueError, TypeError, KeyError) as exc:
            logger.info("dropping invalid triple payload: %s", exc)
            return None

    def extract_text(self, doc_id: str, text: str) -> list[Triple]:
        """Extracts triples from a single document in one completion call.

        Args:
            doc_id: Document identifier stamped onto produced triples.
            text: Raw document text to extract from.

        Returns:
            triples: Validated triples surviving confidence and citation rules.
        """
        prompt = self._build_prompt(text)
        raw = self._complete_with_retry(prompt)
        triples = self._parse_response(raw, doc_id)
        self.stats.triples_extracted += len(triples)
        return triples

    def describe_config(self) -> str:
        """Builds a one-line summary of the active extraction configuration.

        Returns:
            summary: Human-readable description of model and thresholds.
        """
        return (
            f"model={self.config.model} batch_size={self.config.batch_size} "
            f"min_confidence={self.config.min_confidence} "
            f"require_span={self.config.require_source_span}"
        )

    def extract_batch(self, documents: list[tuple[str, str]]) -> list[Triple]:
        """Extracts triples from many documents using batched completions.

        Args:
            documents: (doc_id, text) pairs to extract from.

        Returns:
            triples: All triples from all documents, in input order.
        """
        triples: list[Triple] = []
        for batch in self._batch_documents(documents):
            batch_prompt = self._render_batch_prompt(batch)
            raw = self._complete_with_retry(batch_prompt)
            for doc_id, segment in self._split_batch_response(raw, batch):
                triples.extend(self._parse_response(segment, doc_id))
        self.stats.triples_extracted += len(triples)
        return triples

    def _batch_documents(self, documents: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
        """Groups documents into batches of at most config.batch_size.

        Args:
            documents: (doc_id, text) pairs to group, in order.

        Returns:
            batches: Ordered document groups ready for batched prompting.
        """
        size = max(1, self.config.batch_size)
        return [documents[i : i + size] for i in range(0, len(documents), size)]

    def _render_batch_prompt(self, batch: list[tuple[str, str]]) -> str:
        """Renders one prompt covering several short text windows.

        Args:
            batch: (doc_id, text) pairs to cover in a single completion.

        Returns:
            prompt: Prompt with numbered sections, one per batch member.
        """
        sections = []
        for position, (doc_id, text) in enumerate(batch, start=1):
            sections.append(f"### Document {position} (id: {doc_id})\n{text}")
        joined = "\n\n".join(sections)
        return build_extraction_prompt(joined, self.prompt_config)
