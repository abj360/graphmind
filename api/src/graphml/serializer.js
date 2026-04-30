#!/usr/bin/env node
/**
 * serializer.js --- serializes view graphs into GraphML for downstream tooling
 *  *
 *  * Contains:
 *  *   GRAPHML_HEADER: document prolog and schema keys
 *  *   GRAPHML_FOOTER: document closing tags
 *  *   serializeNode(): renders one node element
 *  *   serializeEdge(): renders one edge element
 *  *   toGraphML(): serializes a full view graph
 */

const GRAPHML_HEADER = `<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="label" for="all" attr.name="label" attr.type="string"/>
  <key id="type" for="node" attr.name="type" attr.type="string"/>
  <key id="predicate" for="edge" attr.name="predicate" attr.type="string"/>
  <key id="confidence" for="edge" attr.name="confidence" attr.type="double"/>`;

const GRAPHML_FOOTER = "</graphml>";

/**
 * Renders one GraphML node element.
 *
 * @param node - View-graph node with id, label, and type.
 * @returns element - Indented GraphML node element string.
 */
export function serializeNode(node) {
  return [
    `    <node id="${node.id}">`,
    `      <data key="label">${node.label}</data>`,
    `      <data key="type">${node.type}</data>`,
    `    </node>`,
  ].join("\n");
}

/**
 * Renders one GraphML edge element.
 *
 * @param edge - View-graph edge with source, target, and predicate.
 * @param index - Position used to build a stable edge id.
 * @returns element - Indented GraphML edge element string.
 */
export function serializeEdge(edge, index) {
  const lines = [
    `    <edge id="e${index}" source="${edge.source}" target="${edge.target}">`,
    `      <data key="predicate">${edge.predicate}</data>`,
  ];
  if (edge.confidence !== null && edge.confidence !== undefined) {
    lines.push(`      <data key="confidence">${edge.confidence}</data>`);
  }
  lines.push("    </edge>");
  return lines.join("\n");
}

/**
 * Serializes a view graph into a complete GraphML document.
 *
 * @param graph - { nodes, edges } payload as served by /api/graph.
 * @returns document - Complete GraphML document string.
 */
export function toGraphML(graph) {
  const nodeElements = graph.nodes.map((node) => serializeNode(node));
  const edgeElements = graph.edges.map((edge, index) => serializeEdge(edge, index));
  return [
    GRAPHML_HEADER,
    '  <graph id="graphmind" edgedefault="directed">',
    ...nodeElements,
    ...edgeElements,
    "  </graph>",
    GRAPHML_FOOTER,
  ].join("\n");
}
