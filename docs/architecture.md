# graphmind architecture overview

One page for orienting in the repo. graphmind turns a directory of text
files into a browsable knowledge graph: chunk text, extract SPO triples
with an LLM, resolve duplicate entities, infer bridging relationships,
load into Neo4j, and explore in a React + Cytoscape.js viewer.

## Pipeline stages

```
text files
  -> extract/chunker.py          sentence-aware overlapping chunks
  -> extract/triple_extractor.py LLM SPO extraction (batched, retried)
  -> extract/ontology.py         schema enforcement rules
  -> extract/relationship_inference.py  bridges between subgraphs
  -> resolution/entity_resolver.py      embedding-based dedup
  -> resolution/alias_table.py          aliases + human merge review
  -> load/neo4j_loader.py        batched upsert writes
  -> load/cdc_poller.py          incremental ingestion
```

## Directory map

- `extract/` — everything between raw text and validated triples.
- `resolution/` — everything about "these two names are the same thing".
- `load/` — everything between resolved triples and Neo4j.
- `api/` — Express BFF: graph JSON, dedup metrics, GraphML export.
- `viz/` — the viewer: Cytoscape canvas, search, legend, detail panel,
  metrics dashboard.
- `docker/` — one Dockerfile per service plus the compose stack.
- `tests/unit`, `tests/integration` — mirrors of the source trees.

## Data shapes that matter

- `Triple` (extract/schema.py) is the contract between stages: subject,
  predicate, object, confidence, source provenance, inferred flag.
- Neo4j stores `:Entity {name, entity_type}` nodes and `:RELATED
  {predicate, confidence, source_doc_id, inferred}` relationships.
- The BFF serves `{nodes, edges}` view graphs; it never exposes Cypher
  to the browser.

## Service topology

Four containers, one compose network: `pipeline` (Python stages plus
CDC poller), `api` (Express BFF on :4000), `viz` (nginx serving the
viewer on :5173), `neo4j` (browser on :7474, bolt on :7687). The viz
container proxies `/api` to the BFF, so the browser only ever talks to
one origin.

## Where the invariants live

- Validation is lossy-by-default but counted, never silent
  (extract/schema.py, ExtractionStats).
- Writes are upsert-only and idempotent (MERGE semantics), so any stage
  can be re-run safely.
- Inferred edges are always marked and always scored, and never merge
  entities by themselves.
- Secrets come from `.env` at runtime; nothing secret is committed.

## What to read first

1. `docs/adr/ADR-001-extraction-and-schema-design.md` for the why.
2. `extract/schema.py` for the what (the data contract).
3. `docker/docker-compose.yml` for the how (the running system).
