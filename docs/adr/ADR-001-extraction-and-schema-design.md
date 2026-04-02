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
