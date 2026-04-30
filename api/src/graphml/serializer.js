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
 *  *   validateGraphInput(): rejects malformed view graphs
 *  *   escapeXml(): escapes XML-special characters in text
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

/**
 * Rejects view graphs whose node/edge references are inconsistent.
 *
 * @param graph - { nodes, edges } payload to validate.
 * @returns graph - The same graph, if valid.
 */
export function validateGraphInput(graph) {
  const nodeIds = new Set(graph.nodes.map((node) => node.id));
  for (const edge of graph.edges) {
    if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
      throw new Error(`edge references unknown endpoint: ${edge.id ?? `${edge.source}->${edge.target}`}`);
    }
  }
  return graph;
}

/**
 * Escapes XML-special characters in arbitrary text.
 *
 * @param text - Raw text that may contain XML metacharacters.
 * @returns escaped - Text safe to embed in XML attributes and content.
 */
export function escapeXml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}
