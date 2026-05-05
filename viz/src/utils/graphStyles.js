#!/usr/bin/env node
/**
 * graphStyles.js --- cytoscape style builders and layout constants for the viewer
 *  *
 *  * Contains:
 *  *   GRAPH_LAYOUT: default force-directed layout options
 *  *   TYPE_COLORS: entity type to color mapping
 *  *   colorForType(): resolves a type to its palette color
 *  *   buildNodeStyle(): cytoscape node style block
 *  *   buildTypeSelectors(): per-type color override selectors
 *  *   buildEdgeStyle(): cytoscape edge style block
 *  *   buildInferredEdgeStyle(): dashed style for inferred edges
 *  *   buildSelfLoopStyle(): curved style for self-loop edges
 */

export const GRAPH_LAYOUT = {
  name: "cose",
  animate: false,
  nodeRepulsion: 8000,
  idealEdgeLength: 120,
  padding: 40,
};

export const TYPE_COLORS = {
  PERSON: "#f4a261",
  ORG: "#2a9d8f",
  GPE: "#e9c46a",
  SOFTWARE: "#457b9d",
  CONCEPT: "#8d99ae",
  GENE: "#9b5de5",
  DISEASE: "#ef476f",
  DRUG: "#06d6a0",
  PATHWAY: "#118ab2",
};

/**
 * Resolves an entity type to its palette color.
 *
 * @param type - Entity type label such as PERSON or ORG.
 * @returns color - Hex color from TYPE_COLORS, grey for unknown types.
 */
export function colorForType(type) {
  return TYPE_COLORS[type] ?? "#6c757d";
}

/**
 * Builds the Cytoscape node style block using the type palette.
 *
 * @returns style - Cytoscape style definition for nodes.
 */
export function buildNodeStyle() {
  return {
    selector: "node",
    style: {
      label: "data(label)",
      "font-size": 10,
      "text-wrap": "wrap",
      "text-max-width": 90,
      "text-valign": "bottom",
      "text-margin-y": 6,
      width: 22,
      height: 22,
      "border-width": 1,
      "border-color": "#1d3557",
    },
  };
}

/**
 * Builds per-type color override selectors for the palette.
 *
 * @returns selectors - Cytoscape style list, one entry per known type.
 */
export function buildTypeSelectors() {
  return Object.entries(TYPE_COLORS).map(([type, color]) => ({
    selector: `node[type = "${type}"]`,
    style: { "background-color": color },
  }));
}

/**
 * Builds the Cytoscape edge style block with arrows and curves.
 *
 * @returns style - Cytoscape style definition for edges.
 */
export function buildEdgeStyle() {
  return {
    selector: "edge",
    style: {
      "curve-style": "bezier",
      "target-arrow-shape": "triangle",
      "arrow-scale": 0.8,
      "line-color": "#adb5bd",
      "target-arrow-color": "#adb5bd",
      width: 2,
      opacity: 0.85,
    },
  };
}

/**
 * Builds the dashed style override for inferred edges.
 *
 * @returns style - Cytoscape style definition for inferred edges.
 */
export function buildInferredEdgeStyle() {
  return {
    selector: "edge[inferred]",
    style: {
      "line-style": "dashed",
      "line-color": "#dee2e6",
      "target-arrow-color": "#dee2e6",
    },
  };
}

/**
 * Builds the loop curve style override for self-loop edges.
 *
 * @returns style - Cytoscape style definition for self-loops.
 */
export function buildSelfLoopStyle() {
  return {
    selector: "edge:loop",
    style: {
      "curve-style": "bezier",
      "loop-direction": "0deg",
      "loop-sweep": "45deg",
    },
  };
}
