# Neo4j ops notes (dev and small-prod)

Running notes for operating the Neo4j instance behind graphmind, written
down the first time each thing bit somebody. Scope: the single-node
community deployment the compose stack runs. Clustering is out of scope.

## Ports and credentials

- 7474: browser and HTTP API. 7687: bolt, the only thing the loader uses.
- Credentials come from `.env` (`NEO4J_USER` / `NEO4J_PASSWORD`), never
  from code. The compose default is a dev password; treat anything
  reachable from a network as needing a real one.
- The loader connects with the service account, not personal accounts —
  personal access is for the browser only.

## Memory sizing

The compose file caps heap at 1G, which is comfortable for the reference
corpus (~120k entities, ~300k relationships). Symptoms you have outgrown
it: long GC pauses in the logs, queries that used to be fast going
multi-second on the same data. Bump `NEO4J_server_memory_heap_max__size`
before touching anything query-side.

## Constraints we rely on

`Entity.name` is unique, enforced by the constraint the loader applies
at connect time. Everything else — idempotent upserts, the dedup
metrics, the resolution pass — assumes that constraint exists. If you
ever drop and recreate the database, the loader recreates the
constraint on its next run; do not create it by hand and forget why.

## Backup routine

`docker/backup.sh` dumps nodes and relationships to a timestamped
archive in the backup volume, verifies the archive, and prunes anything
older than the retention window (default 14 days). Run it from compose:

```bash
docker compose -f docker/docker-compose.yml run --rm backup
```

Verify the archive pool weekly with `docker/verify_backup.sh` — a backup
you have never verified is a rumor, not a backup.

## Restore drill

`docker/restore.sh <archive|latest>` wipes the current graph and replays
an archive. It refuses to run without `GRAPHMIND_RESTORE_CONFIRM=yes`
on purpose. Do a restore drill on a fresh checkout before you need one
for real; the first restore you ever do should not be during an
incident.

## When the graph looks wrong

1. Check duplicate clusters on the metrics dashboard first — a sudden
   jump means entity resolution regressed, not the loader.
2. Spot-check one document: `MATCH ()-[r:RELATED {source_doc_id:
   "path/to/doc.txt"}]->() RETURN r LIMIT 10`. If nothing comes back,
   the document never made it through the loader — check the CDC state
   file before suspecting extraction.
3. If edges exist but look hallucinated, check the extraction stats for
   dropped-low-confidence spikes, then the prompt config — see the
   2026-05-20 citation-requirement fix for the canonical example.

## Upgrades

Neo4j 5 minor upgrades: bump the image tag in compose, recreate the
container, let it migrate the store, confirm the constraint survived.
Major upgrades get a full backup, a restore drill onto the new major
version in a scratch environment, and only then the real move.

## Bulk reloads

A full rebuild from the corpus takes under 3 minutes via the CDC
upsert path; a cold load of a large resolved file takes longer but is
still bounded by batch size, not by RAM. For anything above a few
hundred thousand relationships in one file, raise
`GRAPHMIND_LOAD_BATCH_SIZE` to 1000 and watch the batch latency in the
loader logs.

## Monitoring

There is no separate metrics stack here by design — the signals that
matter are already visible:

- loader logs (batch counts, retries, durations),
- the viewer's dedup metrics dashboard,
- backup job exit codes in cron.

If any of those three goes quiet, that is the alert.

## Common mistakes

- Pointing the loader at 7474 instead of 7687: bolt only, always.
- Deleting nodes to "clean up": delete edges by `source_doc_id` and let
  orphan nodes age out naturally — the resolver may still reference
  them.
- Running backup.sh against the browser port's database container
  without cypher-shell installed: the script checks for it and fails
  fast; install the tools image or use the compose sidecar.

## Data hygiene

The graph is derived state — the corpus is the system of record. That
means: never hand-edit production nodes, never let a one-off script
write without provenance, and treat any edge without `source_doc_id`
as a bug to file, not a fact to keep.

## Useful queries

```cypher
// degree distribution sanity check
MATCH (n:Entity)-[r:RELATED]-()
RETURN n.name, count(r) AS degree ORDER BY degree DESC LIMIT 15

// edges added today
MATCH ()-[r:RELATED]->()
WHERE r.source_doc_id STARTS WITH 'docs/'
RETURN count(r)
```
