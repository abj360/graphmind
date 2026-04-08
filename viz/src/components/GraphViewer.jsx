#!/usr/bin/env node
/**
 * GraphViewer.jsx --- Cytoscape.js canvas rendering the knowledge graph
 *  *
 *  * Contains:
 *  *   toElements(): maps view graph to cytoscape elements
 *  *   GraphViewer: cytoscape canvas component
 *  *   dedupeEdges(): collapses parallel edges between endpoints
 *  *   partitionSelfLoops(): separates self-loops from normal edges
 *  *   curveStyleFor(): picks a curve style per edge index
 *  *   assignParallelIndices(): numbers edges within endpoint groups
 *  *   edgeLabelFor(): compact label for crowded canvases
 */

import cytoscape from "cytoscape";
import { useEffect, useRef } from "react";

import { buildFullStylesheet, GRAPH_LAYOUT } from "../utils/graphStyles.js";

/**
 * Maps a view graph into Cytoscape element definitions.
 *
 * @param graph - { nodes, edges } payload from the BFF.
 * @returns elements - Cytoscape element list.
 */
export function toElements(graph) {
  const nodes = graph.nodes.map((node) => ({
    data: { id: node.id, label: node.label, type: node.type },
  }));
  const edges = graph.edges.map((edge) => ({
    data: {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      predicate: edge.predicate,
      confidence: edge.confidence,
      inferred: edge.inferred,
    },
  }));
  return [...nodes, ...edges];
}

/**
 * Renders the knowledge graph on a Cytoscape canvas.
 *
 * @param props.graph - { nodes, edges } payload to render.
 * @param props.onSelectNode - Callback fired with the tapped node's data.
 * @returns element - Canvas container element.
 */
export default function GraphViewer({ graph, onSelectNode }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    const cy = cytoscape({
      container: containerRef.current,
      elements: toElements(graph),
      layout: GRAPH_LAYOUT,
      style: buildFullStylesheet(),
      wheelSensitivity: 0.2,
    });
    if (onSelectNode) {
      cy.on("tap", "node", (event) => onSelectNode(event.target.data()));
      cy.on("tap", (event) => {
        if (event.target === cy) {
          onSelectNode(null);
        }
      });
    }
    cyRef.current = cy;
    return () => cy.destroy();
  }, [graph, onSelectNode]);

  return <div ref={containerRef} className="graph-canvas" />;
}

/**
 * Collapses parallel edges that share endpoints into single entries.
 *
 * @param edges - Edge list that may contain parallels.
 * @returns edges - One edge per (source, target) pair, labels joined.
 */
export function dedupeEdges(edges) {
  const byPair = new Map();
  for (const edge of edges) {
    const key = `${edge.source}-->${edge.target}`;
    const existing = byPair.get(key);
    if (existing) {
      existing.predicate = `${existing.predicate}, ${edge.predicate}`;
    } else {
      byPair.set(key, { ...edge, id: key });
    }
  }
  return [...byPair.values()];
}

/**
 * Separates self-loop edges from normal edges for distinct styling.
 *
 * @param edges - Full edge list.
 * @returns partitions - { loops, normal } edge lists.
 */
export function partitionSelfLoops(edges) {
  const loops = [];
  const normal = [];
  for (const edge of edges) {
    if (edge.source === edge.target) {
      loops.push(edge);
    } else {
      normal.push(edge);
    }
  }
  return { loops, normal };
}

/**
 * Picks the Cytoscape curve style for an edge among parallel siblings.
 *
 * @param index - Position of the edge within its parallel group.
 * @returns style - bezier for fanned parallels, haystack otherwise.
 */
export function curveStyleFor(index) {
  return index === 0 ? "straight" : "bezier";
}

/**
 * Numbers edges within their (source, target) parallel groups.
 *
 * @param edges - Edge list, possibly containing parallel groups.
 * @returns edges - Edges annotated with parallelIndex and parallelCount.
 */
export function assignParallelIndices(edges) {
  const groups = new Map();
  for (const edge of edges) {
    const key = `${edge.source}-->${edge.target}`;
    const group = groups.get(key) ?? [];
    group.push(edge);
    groups.set(key, group);
  }
  return edges.map((edge) => {
    const group = groups.get(`${edge.source}-->${edge.target}`);
    const parallelIndex = group.indexOf(edge);
    return { ...edge, parallelIndex, parallelCount: group.length };
  });
}

/**
 * Builds a compact edge label for crowded canvases.
 *
 * @param edge - Edge data with predicate and optional confidence.
 * @param showConfidence - Whether to append the confidence score.
 * @returns label - Short label string, possibly empty on dense graphs.
 */
export function edgeLabelFor(edge, showConfidence = false) {
  if (!edge.predicate) {
    return "";
  }
  if (showConfidence && typeof edge.confidence === "number") {
    return `${edge.predicate} (${edge.confidence.toFixed(2)})`;
  }
  return edge.predicate;
}
