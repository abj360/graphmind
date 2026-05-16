# Viewer guide

The graphmind viewer (http://localhost:5173) is the fastest way to see
what the pipeline actually extracted: every entity as a node, every
relationship as an edge, with search, filtering, a detail panel, and a
dedup metrics dashboard. This guide walks the interface top to bottom.

## The canvas

The main area is a Cytoscape.js force-directed canvas. Nodes are
entities, colored by entity type; edges are relationships, labeled with
their predicate when the graph is sparse enough for labels to stay
readable. Drag nodes to pin them, scroll to zoom, drag the background
to pan.

## Layout behavior

- Under ~300 nodes: physics layout (cose) with moderate repulsion.
- Over ~1500 nodes: the viewer switches to a breadth-first layout to
  keep rendering interactive.
- After every data reload the canvas fits to content and clamps zoom
  to a readable range.

## Search and filters

The header search filters the visible graph by entity label or type,
case-insensitively. Only matching nodes and their induced edges stay
visible — the underlying graph is untouched, so clearing the search
restores everything instantly.

## Regex mode

The `.*` toggle next to the search box switches matching from substring
to regular expressions. Invalid patterns fail safe: the filter silently
keeps everything rather than throwing. Handy patterns: `^acme` for
prefixes, `corp|ltd` for suffix families, `^\d{4}` for date-like names.

## The legend

The bottom-left legend lists every entity type present in the current
view with its palette color and node count. Types come from the data,
not a static list, so newly introduced types appear automatically.

## Node detail panel

Clicking a node opens the detail panel in the sidebar: the node's type,
its incident relationships grouped around the selection, and per-edge
confidence badges (green ≥ 0.8, yellow ≥ 0.5, red below). Clicking the
canvas background or the × closes the panel.

## Reading edges

- Solid edges are extracted relationships with confidence-colored lines.
- Dashed edges are *inferred* bridges between subgraphs — hypotheses,
  not facts; treat them accordingly.
- Parallel edges between the same nodes fan out into separate curves;
  their predicates combine when the graph gets dense.

## Metrics dashboard

The sidebar dashboard reports node and edge totals, distinct predicate
count, mean edge confidence, and the duplicate-name clusters the API
finds. Duplicate clusters rising week over week means entity resolution
needs attention — it is the earliest visible symptom.
