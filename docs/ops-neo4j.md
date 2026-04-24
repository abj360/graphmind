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
