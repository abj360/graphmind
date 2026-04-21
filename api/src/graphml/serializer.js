#!/usr/bin/env node
/**
 * serializer.js --- serializes view graphs into GraphML for downstream tooling
 *  *
 *  * Contains:
 *  *   GRAPHML_HEADER: document prolog and schema keys
 *  *   GRAPHML_FOOTER: document closing tags
 *  *   serializeNode(): renders one node element
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
