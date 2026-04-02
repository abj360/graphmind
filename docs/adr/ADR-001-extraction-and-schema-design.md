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
