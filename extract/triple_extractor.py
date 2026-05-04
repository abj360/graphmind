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
    TripleExtractor._split_batch_response(): maps output back to docs
    TripleExtractor.extract_chunks(): extracts from prepared chunks
    calibrate_confidence(): adjusts raw scores for missing citations
    extract_from_documents(): one-shot convenience pipeline
    ExtractionResult: triples bundled with their run stats
    extract_with_result(): extraction returning stats alongside
    merge_extraction_stats(): combines counters across runs
    validate_extraction_config(): rejects inconsistent tunables
    extraction_config_from_env(): builds config from environment
    with_config_overrides(): derives a config with selected changes
    COST_PER_1K_TOKENS: nominal cost model constants
    estimate_extraction_cost(): rough dollar cost of a pass
    redact_prompt_for_logging(): truncates prompts for safe logs
    normalize_document_text(): cleans whitespace before prompting
    build_extractor_from_env(): wires a production extractor
    format_stats_summary(): one-line stats rendering
    build_arg_parser(): CLI argument parser for extraction
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from extract.chunker import TextChunk
from extract.llm_client import LLMClient
from extract.prompts.config import PromptConfig, load_prompt_config
from extract.prompts.templates import build_extraction_prompt
from extract.schema import Triple, clamp_confidence, validate_triple

if TYPE_CHECKING:
    import argparse

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

    @staticmethod
    def _split_batch_response(raw: str, batch: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Associates segments of a batched response with their documents.

        Args:
            raw: Raw batched completion output.
            batch: Documents that were included in the batch prompt.

        Returns:
            segments: (doc_id, response segment) pairs, one per document.
        """
        items = TripleExtractor._extract_json_array(raw)
        if not items or not any("doc_id" in item for item in items):
            return [(batch[0][0], raw)] if batch else []
        segments: list[tuple[str, str]] = []
        for doc_id, _ in batch:
            own = [item for item in items if item.get("doc_id") == doc_id]
            segments.append((doc_id, json.dumps(own)))
        return segments

    def extract_chunks(self, chunks: list[TextChunk]) -> list[Triple]:
        """Extracts triples from pre-chunked text, batching when beneficial.

        Args:
            chunks: Prepared TextChunks from the chunking pass.

        Returns:
            triples: All extracted triples across the chunk set.
        """
        if len(chunks) <= self.config.batch_size:
            triples: list[Triple] = []
            for chunk in chunks:
                triples.extend(self.extract_text(chunk.doc_id, chunk.text))
            return triples
        documents = [(chunk.doc_id, chunk.text) for chunk in chunks]
        return self.extract_batch(documents)


def calibrate_confidence(raw_score: float, has_span: bool) -> float:
    """Adjusts a raw model-reported score using citation presence.

    Args:
        raw_score: Model-reported confidence, possibly out of range.
        has_span: Whether the triple carries a source-span citation.

    Returns:
        calibrated: Clamped score, discounted when no citation exists.
    """
    score = clamp_confidence(raw_score)
    if not has_span:
        score *= 0.8
    return round(score, 4)


def extract_from_documents(
    client: LLMClient,
    documents: list[tuple[str, str]],
    config: ExtractionConfig | None = None,
) -> list[Triple]:
    """Runs chunk-free extraction over documents with a fresh extractor.

    Args:
        client: Completion provider used for extraction prompts.
        documents: (doc_id, text) pairs to extract from.
        config: Extraction tunables; defaults applied when omitted.

    Returns:
        triples: All extracted triples across the document set.
    """
    extractor = TripleExtractor(client, config)
    return extractor.extract_batch(documents)


@dataclass(frozen=True)
class ExtractionResult:
    """Bundles extracted triples with the stats of the producing run.

    Attributes:
        triples: Triples produced by the run.
        stats: Counters describing the run.
    """

    triples: list[Triple]
    stats: ExtractionStats


def extract_with_result(extractor: TripleExtractor, doc_id: str, text: str) -> ExtractionResult:
    """Runs extraction and returns triples bundled with run stats.

    Args:
        extractor: Extractor instance to run.
        doc_id: Document identifier stamped onto produced triples.
        text: Raw document text to extract from.

    Returns:
        result: Triples bundled with the producing run's counters.
    """
    triples = extractor.extract_text(doc_id, text)
    return ExtractionResult(triples=triples, stats=extractor.stats)


def merge_extraction_stats(target: ExtractionStats, source: ExtractionStats) -> ExtractionStats:
    """Merges one stats counter set into another.

    Args:
        target: Counter set accumulating the combined totals.
        source: Counter set whose values are added in.

    Returns:
        target: The mutated target, for convenient chaining.
    """
    target.calls_made += source.calls_made
    target.triples_extracted += source.triples_extracted
    target.retries += source.retries
    target.dropped_low_confidence += source.dropped_low_confidence
    target.dropped_missing_span += source.dropped_missing_span
    return target


def validate_extraction_config(config: ExtractionConfig) -> ExtractionConfig:
    """Rejects extraction configurations that cannot work as requested.

    Args:
        config: Candidate extraction configuration.

    Returns:
        config: The same configuration, if valid.
    """
    if not 0.0 <= config.min_confidence <= 1.0:
        msg = f"min_confidence {config.min_confidence} outside [0, 1]"
        raise ValueError(msg)
    if config.batch_size < 1:
        msg = f"batch_size {config.batch_size} must be at least 1"
        raise ValueError(msg)
    if config.max_retries < 0:
        msg = f"max_retries {config.max_retries} must not be negative"
        raise ValueError(msg)
    return config


def extraction_config_from_env(env: dict[str, str]) -> ExtractionConfig:
    """Builds an ExtractionConfig from GRAPHMIND_EXTRACT_* overrides.

    Args:
        env: Environment mapping to read overrides from.

    Returns:
        config: Validated extraction configuration.
    """
    config = ExtractionConfig(
        model=env.get("GRAPHMIND_EXTRACT_MODEL", DEFAULT_MODEL),
        max_retries=int(env.get("GRAPHMIND_EXTRACT_MAX_RETRIES", "2")),
        batch_size=int(env.get("GRAPHMIND_EXTRACT_BATCH_SIZE", "8")),
        min_confidence=float(env.get("GRAPHMIND_EXTRACT_MIN_CONFIDENCE", "0.0")),
        require_source_span=env.get("GRAPHMIND_EXTRACT_REQUIRE_SPAN", "false") == "true",
    )
    return validate_extraction_config(config)


def with_config_overrides(config: ExtractionConfig, **overrides: Any) -> ExtractionConfig:
    """Derives a new ExtractionConfig with selected fields replaced.

    Args:
        config: Base configuration to copy.
        overrides: Field names and replacement values.

    Returns:
        config: New validated configuration with overrides applied.
    """
    from dataclasses import replace

    return validate_extraction_config(replace(config, **overrides))


COST_PER_1K_INPUT_TOKENS = 0.00015
COST_PER_1K_OUTPUT_TOKENS = 0.0006


def estimate_extraction_cost(total_chars: int, config: ExtractionConfig) -> float:
    """Estimates the dollar cost of extracting from a character volume.

    Args:
        total_chars: Total source characters to process.
        config: Extraction configuration influencing batching overhead.

    Returns:
        cost: Approximate dollar cost of the full extraction pass.
    """
    input_tokens = total_chars / 4
    prompt_overhead_tokens = 400 * (input_tokens / (config.batch_token_budget or 6_000) + 1)
    output_tokens = input_tokens * 0.3
    cost = (input_tokens + prompt_overhead_tokens) / 1000 * COST_PER_1K_INPUT_TOKENS
    return cost + output_tokens / 1000 * COST_PER_1K_OUTPUT_TOKENS


def redact_prompt_for_logging(prompt: str, max_length: int = 200) -> str:
    """Truncates a rendered prompt so logs stay readable and small.

    Args:
        prompt: Rendered prompt about to be logged.
        max_length: Maximum characters kept before the ellipsis.

    Returns:
        redacted: Prompt truncated to max_length with an ellipsis marker.
    """
    if len(prompt) <= max_length:
        return prompt
    return prompt[:max_length] + "...[truncated]"


def normalize_document_text(text: str) -> str:
    """Collapses pathological whitespace before text reaches the prompt.

    Args:
        text: Raw document text, possibly with noisy spacing.

    Returns:
        normalized: Text with collapsed blank lines and trailing spaces.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    collapsed = "\n".join(lines)
    while "\n\n\n" in collapsed:
        collapsed = collapsed.replace("\n\n\n", "\n\n")
    return collapsed.strip()


def build_extractor_from_env(env: dict[str, str]) -> TripleExtractor:
    """Wires a production TripleExtractor from environment configuration.

    Args:
        env: Environment mapping carrying model and provider settings.

    Returns:
        extractor: Fully wired extractor with a LangChain-backed client.
    """
    from extract.llm_client import build_default_client

    config = extraction_config_from_env(env)
    client = build_default_client(config.model)
    return TripleExtractor(client, config)


def format_stats_summary(stats: ExtractionStats) -> str:
    """Renders extraction stats as a single log-friendly line.

    Args:
        stats: Counters to summarize.

    Returns:
        summary: One-line rendering of calls, triples, and drops.
    """
    return (
        f"calls={stats.calls_made} triples={stats.triples_extracted} "
        f"retries={stats.retries} dropped_low_conf={stats.dropped_low_confidence} "
        f"dropped_missing_span={stats.dropped_missing_span}"
    )


def build_arg_parser() -> "argparse.ArgumentParser":
    """Builds the command-line argument parser for the extraction CLI.

    Returns:
        parser: Configured ArgumentParser for corpus extraction runs.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Extract SPO triples from a corpus")
    parser.add_argument("--corpus", required=True, help="directory of .txt documents")
    parser.add_argument("--out", default="out/triples.jsonl", help="output JSONL path")
    parser.add_argument("--batch-size", type=int, default=8, help="chunks per batch")
    return parser
