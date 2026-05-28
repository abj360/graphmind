#!/usr/bin/env node
/**
 * graphml.roundtrip.test.js --- roundtrip tests proving GraphML output is valid XML
 *  *
 *  * Contains:
 *  *   test: special characters are escaped in output
 */

import assert from "node:assert/strict";
import test from "node:test";

import { escapeXml, toGraphML } from "../src/graphml/serializer.js";

test("special characters in labels are escaped in GraphML output", () => {
  const document = toGraphML({
    nodes: [{ id: 'A & "B" <C>', label: 'A & "B" <C>', type: "ORG" }],
    edges: [],
  });
  assert.doesNotMatch(document, /A & "B"/);
  assert.match(document, /A &amp; &quot;B&quot; &lt;C&gt;/);
});
