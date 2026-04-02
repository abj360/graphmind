#!/usr/bin/env node
/**
 * serializer.js --- serializes view graphs into GraphML for downstream tooling
 *  *
 *  * Contains:
 *  *   GRAPHML_HEADER: document prolog and schema keys
 */

const GRAPHML_HEADER = `<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="label" for="all" attr.name="label" attr.type="string"/>
  <key id="type" for="node" attr.name="type" attr.type="string"/>
  <key id="predicate" for="edge" attr.name="predicate" attr.type="string"/>
  <key id="confidence" for="edge" attr.name="confidence" attr.type="double"/>`;
