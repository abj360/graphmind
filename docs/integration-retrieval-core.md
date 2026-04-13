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

## When the graph path should answer

Route a query to the graph when **all** of the following hold:

1. The question mentions two or more recognizable entities, or asks for
   a relationship ("who founded X", "what does Y depend on").
2. Recall matters more than latency: graph expansion costs a round trip
   to Neo4j that BM25 does not need.
3. The entities plausibly exist in the corpus the graph was built from.

Do not route single-entity lookup questions — retrieval-core's primary
path already wins those. The graph path is a *complement*, never a
replacement.

## Architecture: how the two systems connect

```
query ──► retrieval-core ──► entity linker ──► graphmind Neo4j
                │                                  │
                │◄── grounded passages ◄── edge provenance
                ▼
           fused answer
```

- retrieval-core owns the user-facing query interface.
- A lightweight entity linker (retrieval-core side) maps query mentions
  to candidate canonical entity names.
- graphmind's Neo4j is queried read-only with those names as anchors.
- Returned edges carry `source_doc_id`, which retrieval-core resolves
  back into passages through its own document store.

graphmind never calls retrieval-core; the dependency is one-directional.

## The anchor query: one-hop expansion

The workhorse query expands one hop around an anchored entity:

```cypher
MATCH (a:Entity {name: $name})-[r:RELATED]-(b:Entity)
RETURN a.name AS anchor, r.predicate AS predicate, b.name AS neighbor,
       r.confidence AS confidence, r.source_doc_id AS doc_id
ORDER BY r.confidence DESC
LIMIT $limit
```

Notes:

- The relationship pattern is undirected here (`-[r:RELATED]-`): the
  question "what involves X" does not care about edge direction.
- Results are ordered by confidence so a noisy long tail never drowns
  the strong edges.
- `$limit` is a parameter, never string-interpolated — same rule as
  everywhere else: no query text built by concatenating user input.

## The bridge query: two-hop paths between entities

For "how are A and B related" the integration uses a bounded shortest
path:

```cypher
MATCH path = shortestPath(
  (a:Entity {name: $left})-[:RELATED*..3]-(b:Entity {name: $right})
)
RETURN [n IN nodes(path) | n.name] AS nodes,
       [r IN relationships(path) | r.predicate] AS predicates
LIMIT 3
```

The hop bound (`*..3`) is deliberate: unbounded `shortestPath` on a
densely bridged graph is how you get a query that never comes back.
Three hops covers the useful cases (A–bridge–B, A–mid–mid–B) while
keeping worst-case expansion small.
