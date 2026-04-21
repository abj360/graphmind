# ADR-001: Extraction and Schema Design

- Status: accepted
- Date: 2026-04-02
- Deciders: Peter (ML & retrieval), Angel (DevOps/security), Yannick (full-stack)

## Context

graphmind turns unstructured text into a property graph in Neo4j. The
pipeline has five stages: chunking, LLM-based SPO triple extraction,
embedding-based entity resolution, relationship inference, and batched
loading. This ADR records the load-bearing decisions in the extraction
and schema layers, where mistakes are the most expensive to unwind
later: a schema decision made in week one shapes every downstream
consumer of the graph.

## Decision: pydantic models are the single contract

`extract/schema.py` is the one place where the shape of a `Triple` is
defined. Every stage takes and returns these models; nothing passes
around raw dicts between stages. Rationale:

- Validation failures surface at the stage boundary that caused them,
  not three stages later in the loader.
- Frozen models (`ConfigDict(frozen=True)`) keep stages honest about
  not mutating shared state — most of the concurrency bugs we have
  lived through elsewhere came from mutable shared payloads.
- The loader's row shapes derive from the same models, so the Cypher
  layer cannot drift from the extraction layer silently.

## Decision: triples carry provenance and confidence from birth

Every triple has `source_doc_id`, an optional `source_span`, a
`confidence` in `[0, 1]`, and an `inferred` flag. Alternatives
considered:

- Attach provenance in a sidecar table: rejected — provenance is not
  optional metadata; it is how reviewers decide whether to trust an
  edge. If it can be forgotten, it will be.
- Add confidence later once scoring stabilizes: rejected — retrofitting
  a float column through five stages is exactly the kind of change that
  looks small and isn't. Confidence is present from the first triple,
  defaulting to 1.0 so early extractors remain valid.

## Decision: the extractor depends on a protocol, not a vendor

`TripleExtractor` takes any `LLMClient` — a Python `Protocol` with one
method, `complete(prompt) -> str`. Production wiring adapts a LangChain
chat model (`LangChainClient`); tests use scripted fakes. The extractor
never imports LangChain itself.

Consequences:

- Provider swaps (OpenAI today, anything else later) touch one adapter.
- Tests assert on the exact prompt text the model saw, which is where
  extraction quality actually lives.
- There is no hidden global client: dependency injection is explicit,
  per the engineering standards.

## Decision: prompt configuration is decoupled from extraction logic

Prompt wording changes an order of magnitude more often than extraction
logic. `extract/prompts/` therefore owns templates and a `PromptConfig`
dataclass loaded from TOML (`default.toml`), and the extractor only
asks for "the prompt for this text". Domain variants (technical, news,
biomedical) are registered hints plus matched few-shot examples, not
forked template copies.

Rejected alternative: one canonical prompt with if/else branches per
domain — it accretes conditionals until nobody can tell which wording
shipped in which run.

## Decision: validation is lossy by default, strict on demand

`validate_triples()` drops invalid items and keeps going;
`validate_triples_strict()` aggregates every failure and raises.
Rationale: an LLM that returns 19 good triples and 1 malformed one
should yield 19 triples, not zero — but a caller that *needs*
all-or-nothing (e.g. a conformance test) can get it explicitly.

This mirrors the fail-closed principle in the engineering standards:
the *default* path degrades visibly (drops are logged and counted in
`ExtractionStats`), never silently.

## Decision: ontology enforcement happens after extraction, not inside it

The ontology (`extract/ontology.py`) is a set of
`(subject_type, predicate, object_type)` rules applied as a separate
pass over validated triples. Extraction stays ontology-agnostic so the
same extractor serves domains with no rule set at all.

Enforcement returns `(kept, violations)` rather than raising: a
rejected triple is data (something the model saw that our schema
forbids) and reviewers want the rejection list, not an exception.
