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
