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

## Handling inferred edges

Bridging relationships produced by `relationship_inference.py` carry
`inferred: true` and a capped confidence. The integration's policy:

- Inferred edges may *support* an answer, never *be* the answer alone:
  a path consisting only of inferred edges is treated as "no answer".
- When an inferred edge is used, the response marks it as inferred so
  the caller can hedge appropriately ("likely related", not "related").

This is the query-side mirror of the viewer rendering inferred edges
dashed: the graph contains hypotheses, and consumers must know which
edges they are.

## Grounding back into passages

Every edge returned by Neo4j carries `source_doc_id`. retrieval-core
uses it to fetch the originating passage and present the graph answer
with a citation:

1. Run the anchor or bridge query.
2. Collect distinct `source_doc_id` values from returned edges.
3. Resolve those ids through retrieval-core's document store.
4. Attach the passages to the answer as citations.

Edges with `source_doc_id = "__inference__"` (inferred bridges) have no
passage by construction — they ground through their *endpoint*
entities' documents instead.

## Confidence thresholds

The integration filters edges client-side after the query:

- Below 0.5: dropped entirely — more noise than signal.
- 0.5–0.7: usable as supporting evidence only.
- Above 0.7: usable as primary evidence.

These thresholds are the query-side counterpart of the extraction-side
`min_confidence` floor. They intentionally differ: extraction keeps a
wider net, the query path presents a stricter one.

## Failure modes and fallbacks

| Failure | Behavior |
| --- | --- |
| Neo4j unreachable | Log, mark graph path degraded, answer via primary path only |
| Anchor entity not found | Fall back to primary path; do not fuzzy-match silently |
| Query exceeds latency budget | Cancel, return partial answer, record the timeout |
| Empty graph (pre-ingestion) | Graph path reports itself empty; no error surfaced to users |

The integration fails *open to the primary path* for availability but
*closed on correctness*: a degraded graph answer is worse than no graph
answer, because a wrong relationship stated confidently is the hardest
bug to un-ship.

## Latency budget

Measured on the reference corpus (~120k entities, ~300k edges):

| Query shape | p50 | p95 |
| --- | --- | --- |
| Anchor (one-hop) | 8 ms | 40 ms |
| Bridge (bounded path) | 25 ms | 180 ms |
| Grounding fan-out | 15 ms | 90 ms |

The bridge query dominates. If p95 ever matters to the user-facing SLO,
the answer is a tighter hop bound or a precomputed neighborhood cache —
not a bigger budget.

## Local development setup

Everything runs from the compose stack; nothing is installed locally:

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
```

- Viewer: http://localhost:5173
- BFF: http://localhost:4000 (`/api/graph`, `/api/metrics/dedup`,
  `/api/export/graphml`)
- Neo4j browser: http://localhost:7474 (credentials from `.env`)

Load a corpus by dropping `.txt` files into the `corpus_data` volume's
source directory and letting the CDC poller pick them up, or by running
the pipeline stages manually (see below).

## Running the pipeline by hand

```bash
docker compose -f docker/docker-compose.yml exec pipeline \
  python -m extract.triple_extractor --corpus /data/docs
docker compose -f docker/docker-compose.yml exec pipeline \
  python -m resolution.entity_resolver --graph /out/triples.jsonl
docker compose -f docker/docker-compose.yml exec pipeline \
  python -m load.neo4j_loader --input /out/resolved.jsonl
```

Each stage reads the previous stage's JSONL output, so a stage can be
re-run without redoing the whole pipeline.

## Testing the integration point

The contract between the two repos is the *schema*, not a client
library:

- graphmind guarantees the `:Entity`/`:RELATED` shape and the
  provenance fields documented above.
- retrieval-core treats anything else as internal and subject to
  change.

A breaking schema change (renaming a property, changing id semantics)
is a coordinated, versioned event: bump the graph schema version,
migrate the data, then update the consumer — in that order.

## Operational notes

- Backups: `docker/backup.sh` produces timestamped archives and prunes
  by retention window; restore is deliberately gated behind an explicit
  confirmation flag.
- The graph is rebuildable from the corpus at any time; treat Neo4j as
  derived state, not a system of record.
- Watch the duplicate-cluster count on the viewer's metrics dashboard:
  a rising trend means resolution thresholds need attention before the
  graph path's answers get weird.

## Entity linking contract

The linker (retrieval-core side) turns query text into anchor names:

- Exact match first: the query's capitalized spans are looked up against
  `:Entity.name` directly.
- Alias match second: the alias table (`resolution/alias_table.py`) is
  consulted so "ACME Corp" anchors to the same node as "Acme
  Corporation".
- No embedding match on the query path: anchor candidates that need
  embedding search are too uncertain to expand from and are better
  served by the primary path.

The linker returns at most three anchors; more than that and the
expansion cost stops paying for itself.

## Worked example: "who founded Acme?"

1. Linker anchors `Acme` to the canonical node `acme`.
2. Anchor query runs with a predicate hint (`founded`); the returned
   edge `(alice)-[founded]->(acme)` has confidence 0.97 and
   `source_doc_id = docs/news-041.txt`.
3. retrieval-core fetches the passage, attaches it as a citation.
4. Answer: "Alice founded Acme", with the passage quoted and the edge
   confidence shown to reviewers on demand.

## Worked example: "what does the export service depend on?"

1. Linker anchors `export service` (SOFTWARE).
2. One-hop expansion returns `depends on` edges to `neo4j`, `express`,
   and an inferred `associated with` edge to `graph viewer`.
3. The inferred edge is excluded from the headline answer but listed
   under "possibly related" — the hedge is the feature.

## Freshness expectations

The CDC poller keeps the graph within one polling interval of the
corpus (default 5s) plus extraction latency (seconds per changed
document). retrieval-core should therefore assume:

- New documents are queryable in the graph within roughly a minute.
- Deleted documents' edges disappear on the same schedule.
- A full rebuild (disaster recovery) takes under 3 minutes on the
  reference corpus via the upsert-only path.

If retrieval-core observes graph answers contradicting freshly ingested
documents, check the CDC state file before assuming an extraction bug.

## Monitoring the graph path

Metrics worth alarming on, all available without new instrumentation:

- Graph path latency p95 vs the budget table above.
- Share of queries with zero anchors (rising trend = linker drift or
  corpus drift).
- Neo4j pool wait time (rising = connection starvation under fan-out).
- Duplicate-cluster count on the viewer dashboard (rising = resolution
  regression; see the 2026-05-06 incident).

## Security notes

- The integration account is read-only; writes happen only through the
  pipeline's own loader credentials.
- Query parameters are always driver parameters — the day someone
  concatenates user text into Cypher is the day we get an injection
  incident report.
- Graph contents inherit corpus sensitivity: if a document shouldn't
  be queryable, it shouldn't be in the corpus, because its facts will
  be in the graph.

## Schema versioning

| Version | Change | Consumer action |
| --- | --- | --- |
| 1 | `:Entity{name, entity_type}`, `:RELATED{predicate, confidence, source_doc_id}` | none |
| 2 | adds `inferred` on `:RELATED` | filter/flag inferred edges |
| 3 | adds `source_span` on extraction-produced edges | optional citation display |

Consumers pin to a major version; additions are minor, removals or
renames are major and coordinated as described in "Testing the
integration point".

## Caching guidance

- Anchor lookups cache well: entity names change rarely; a 5-minute TTL
  is safe and cuts repeat latency sharply.
- Bridge queries cache poorly across corpus updates; key any cache on
  the CDC state's max `modified_at`, or don't cache at all.
- Never cache "entity not found" for longer than a polling interval —
  that is how you get ghost misses after a document lands.

## Load characteristics

Under the reference query mix (70% anchor, 20% bridge, 10% grounding
fan-out):

- Neo4j stays under 20% heap at 50 queries/second.
- The binding constraint is connection checkout during fan-out bursts;
  size the pool for the p99 fan-out, not the average.
- The BFF adds ~2 ms per hop; it is never the bottleneck and should not
  be scaled before Neo4j is.
