#!/usr/bin/env node
/**
 * serializer.test.js --- unit tests for the GraphML serializer
 *  *
 *  * Contains:
 *  *   test: serializeNode renders label and type
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
