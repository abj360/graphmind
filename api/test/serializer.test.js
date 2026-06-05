#!/usr/bin/env node
/**
 * serializer.test.js --- unit tests for the GraphML serializer
 *  *
 *  * Contains:
 *  *   test: serializeNode renders label and type
 *  *   test: serializeEdge omits missing confidence
 *  *   test: toGraphML wraps nodes and edges in a graph element
 *  *   test: validateGraphInput rejects dangling edges
 *  *   test: escapeXml covers all five metacharacters
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  escapeXml,
  serializeEdge,
  serializeNode,
  toGraphML,
  validateGraphInput,
} from "../src/graphml/serializer.js";

test("serializeNode renders label and type data", () => {
  const element = serializeNode({ id: "Acme", label: "Acme", type: "ORG" });
  assert.match(element, /<node id="Acme">/);
  assert.match(element, /<data key="type">ORG<\/data>/);
});

test("serializeEdge omits the confidence data when absent", () => {
  const element = serializeEdge({ source: "A", target: "B", predicate: "p" }, 0);
  assert.doesNotMatch(element, /confidence/);
  const withConfidence = serializeEdge({ source: "A", target: "B", predicate: "p", confidence: 0.5 }, 1);
  assert.match(withConfidence, /<data key="confidence">0.5<\/data>/);
});

test("toGraphML wraps nodes and edges in a graph element", () => {
  const document = toGraphML({
    nodes: [{ id: "A", label: "A", type: "ORG" }],
    edges: [{ source: "A", target: "A", predicate: "p" }],
  });
  assert.match(document, /^<\?xml version="1.0"/);
  assert.match(document, /<\/graphml>$/);
  assert.match(document, /<edge id="e0"/);
});

test("validateGraphInput rejects edges with unknown endpoints", () => {
  assert.throws(() =>
    validateGraphInput({
      nodes: [{ id: "A", label: "A", type: "ORG" }],
      edges: [{ id: "e0", source: "A", target: "ghost", predicate: "p" }],
    }),
  );
});

test("escapeXml escapes all five XML metacharacters", () => {
  assert.equal(escapeXml(`<a b="c">&'</a>`), "&lt;a b=&quot;c&quot;&gt;&amp;&apos;&lt;/a&gt;");
});
