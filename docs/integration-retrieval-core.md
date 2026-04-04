# Integrating graphmind with retrieval-core

This document describes how the knowledge graph produced by graphmind is
queried as a **secondary retrieval path** from `retrieval-core`: when it
helps, how the query path is shaped, what the operational constraints
are, and how to run the whole thing locally.

Audience: engineers working on either repo. Familiarity with Cypher is
assumed at the "can read a MATCH" level.

## Why a graph path at all

retrieval-core answers "what documents are about X" extremely well. It
answers "how is A related to B" poorly, because that question is not a
similarity question — it is a connectivity question. The graphmind
knowledge graph exists precisely for the second shape:

- Entities are nodes (`:Entity` with `name` and `entity_type`).
- Relationships are edges (`:RELATED` with `predicate`, `confidence`,
  `source_doc_id`, and `inferred`).
- Every edge traces back to the document it came from, so a graph answer
  can always be grounded back into retrieval-core's document space.
