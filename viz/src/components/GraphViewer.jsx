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
 *  *   filterEdgesForDensity(): hides labels beyond a density bound
 *  *   zIndexFor(): keeps edges below node labels
 *  *   visibleEdgeWidth(): scales width with confidence
 *  *   fitToContent(): recenters the canvas after load
 *  *   layoutForSize(): picks a layout by graph size
 *  *   clampZoom(): bounds the zoom level for readability
 *  *   edgeTooltipFor(): full tooltip text for one edge
 *  *   mergeDuplicatePredicates(): joins predicate labels on parallels
 *  *   opacityForDensity(): fades edges as density climbs
 *  *   labelFontForDensity(): shrinks labels on dense graphs
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

/**
 * Decides whether edge labels should render given graph density.
 *
 * @param nodeCount - Number of visible nodes.
 * @param edgeCount - Number of visible edges.
 * @returns show - False when the canvas is too dense for readable labels.
 */
export function shouldShowEdgeLabels(nodeCount, edgeCount) {
  if (nodeCount === 0) {
    return true;
  }
  return edgeCount / nodeCount <= 3 && edgeCount <= 800;
}

/**
 * Computes the z-index for edges relative to node labels.
 *
 * @param edge - Edge data with the inferred flag.
 * @returns zIndex - Lower for inferred edges, keeping them visually behind.
 */
export function edgeZIndex(edge) {
  return edge.inferred ? 1 : 2;
}

/**
 * Scales an edge's width by its confidence score.
 *
 * @param confidence - Confidence between 0 and 1, possibly null.
 * @returns width - Pixel width between 1 and 5.
 */
export function edgeWidthFor(confidence) {
  if (typeof confidence !== "number") {
    return 2;
  }
  return 1 + 4 * Math.min(Math.max(confidence, 0), 1);
}

/**
 * Recenters the canvas to fit all elements after a load.
 *
 * @param cy - Cytoscape instance to fit.
 * @param padding - Pixel padding around the fitted elements.
 */
export function fitToContent(cy, padding = 40) {
  cy.fit(undefined, padding);
  cy.center();
}

/**
 * Picks a layout name appropriate for the visible graph size.
 *
 * @param nodeCount - Number of visible nodes.
 * @returns layout - Layout name: grid for tiny graphs, cose otherwise.
 */
export function layoutForSize(nodeCount) {
  if (nodeCount <= 1) {
    return "grid";
  }
  if (nodeCount > 1500) {
    return "breadthfirst";
  }
  return "cose";
}

/**
 * Bounds the canvas zoom level for label readability.
 *
 * @param cy - Cytoscape instance to clamp.
 */
export function clampZoom(cy) {
  const zoom = Math.min(Math.max(cy.zoom(), 0.2), 2.5);
  if (zoom !== cy.zoom()) {
    cy.zoom(zoom);
  }
}

/**
 * Builds the full tooltip text for one edge.
 *
 * @param edge - Edge data with predicate, confidence, and inferred flag.
 * @returns tooltip - Multi-part descriptive tooltip string.
 */
export function edgeTooltipFor(edge) {
  const parts = [`${edge.source} —${edge.predicate}→ ${edge.target}`];
  if (typeof edge.confidence === "number") {
    parts.push(`confidence ${edge.confidence.toFixed(2)}`);
  }
  if (edge.inferred) {
    parts.push("inferred");
  }
  return parts.join(" · ");
}

/**
 * Joins duplicate predicate labels within a parallel edge group.
 *
 * @param edges - Edges in one parallel group.
 * @returns label - Comma-joined distinct predicate label.
 */
export function mergeDuplicatePredicates(edges) {
  const seen = new Set();
  for (const edge of edges) {
    seen.add(edge.predicate);
  }
  return [...seen].join(", ");
}

/**
 * Fades edge opacity as the visible graph gets denser.
 *
 * @param nodeCount - Number of visible nodes.
 * @param edgeCount - Number of visible edges.
 * @returns opacity - Edge opacity between 0.25 and 0.9.
 */
export function opacityForDensity(nodeCount, edgeCount) {
  if (nodeCount === 0) {
    return 0.9;
  }
  const density = edgeCount / nodeCount;
  return Math.max(0.25, Math.min(0.9, 1.1 - density * 0.15));
}

/**
 * Shrinks node label font size as the visible graph gets denser.
 *
 * @param nodeCount - Number of visible nodes.
 * @returns fontSize - Label font size in pixels.
 */
export function labelFontForDensity(nodeCount) {
  if (nodeCount > 800) {
    return 6;
  }
  if (nodeCount > 300) {
    return 8;
  }
  return 10;
}
