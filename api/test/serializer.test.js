#!/usr/bin/env node
/**
 * serializer.test.js --- unit tests for the GraphML serializer
 *  *
 *  * Contains:
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
