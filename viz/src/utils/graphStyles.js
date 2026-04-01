#!/usr/bin/env node
/**
 * graphStyles.js --- cytoscape style builders and layout constants for the viewer
 *  *
 *  * Contains:
 *  *   GRAPH_LAYOUT: default force-directed layout options
 *  *   TYPE_COLORS: entity type to color mapping
 *  *   colorForType(): resolves a type to its palette color
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
