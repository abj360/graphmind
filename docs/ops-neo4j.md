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
