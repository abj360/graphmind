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
