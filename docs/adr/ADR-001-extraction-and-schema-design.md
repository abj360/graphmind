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

## Decision: inferred bridging edges are marked, capped, and scored

Relationship inference bridges disconnected components so the graph is
navigable end to end. Inferred triples:

- are flagged `inferred=True` at the schema level,
- carry a heuristic confidence capped at 0.95 — below most extracted
  edges, deliberately,
- are bounded per component pair (`candidate_limit`) so a hub-heavy
  graph cannot explode combinatorially,
- render dashed in the viewer so reviewers can tell them apart at a
  glance.

## Decision: entity resolution is embedding-based with a human review queue

Naive string matching (the initial implementation) misses trivially
different surface forms of the same entity — "Acme Corp" vs "Acme
Corporation" — and produced a roughly 3x duplicate-node explosion on
the first real corpus (fixed 2026-05-06). Resolution now embeds entity
names and union-finds pairs above a cosine threshold.

Crucially, the band between `review_floor` and `threshold` is not
auto-merged: those pairs go to `MergeReviewQueue` for a human decision
that lands in the alias table. Fully automatic merging of proper nouns
is how you end up with two different people collapsed into one node.

## Consequences: costs we accepted

- Five stages means five places to instrument; `ExtractionStats`,
  `LoadStats`, and the resolution report exist precisely so no stage is
  a black box.
- The prompt-as-data split means prompt regressions are config changes,
  not code changes — including the 2026-05-20 fix where prompts had to
  start *requiring* source-span citations because the extractor was
  hallucinating relationships not present in the text. That class of
  bug is why `require_source_span` exists as a first-class switch.
- Frozen pydantic models mean more `replace()` calls than mutation;
  measured overhead is irrelevant next to LLM latency.

## Consequences: what this buys us

- Every edge in Neo4j can be traced to a document, and (when citations
  are required) to an exact passage.
- The viewer, the GraphML export, and the retrieval-core integration
  all consume the same schema — no per-consumer translation layers.
- Tests run fully offline: deterministic fakes for the LLM and a
  recording double for the Neo4j driver.

## Alternatives considered: property graph vs RDF triplestore

We chose Neo4j's labelled property graph over an RDF store. The queries
this project actually runs (neighborhood expansion for the viewer,
path-finding for the integration, type/predicate aggregations for the
metrics dashboard) are Cypher-shaped; OWL reasoning is out of scope,
and the team already operates Neo4j in production.

## Alternatives considered: batch vs streaming extraction

Extraction is a batch pass over chunks, not a streaming pipeline. The
corpus is bounded and rebuilds were initially full re-runs; incremental
freshness is handled by CDC polling with upsert-only writes (see
`load/cdc_poller.py`), which cut graph rebuild time from ~40 minutes to
under 3 — streaming infrastructure would have added brokers and
exactly-once semantics for no measurable gain at this corpus size.

## Notes: batching and retries

- LLM calls retry transient failures with bounded attempts; persistent
  failure raises `ExtractionError` rather than returning partial junk.
- Neo4j writes are batched UNWIND upserts (`MERGE` semantics) so
  re-running a document is idempotent.
- Batch sizes are configuration, not constants: the right number on a
  laptop and in CI are not the same number.

## Notes: what would change our mind

- If consumers start needing reification beyond confidence/provenance
  (e.g. temporal validity on edges), RDF + named graphs becomes worth
  re-evaluating.
- If the corpus grows past what periodic full snapshots handle, the CDC
  path becomes the primary ingestion path and the batch extractor
  becomes a backfill tool.
- If auto-merge precision measurably exceeds human review quality on
  the borderline band, the review floor moves — with data, not vibes.
