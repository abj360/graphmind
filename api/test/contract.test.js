#!/usr/bin/env node
/**
 * contract.test.js --- contract tests for the BFF HTTP endpoints
 *  *
 *  * Contains:
 *  *   test: health endpoint returns ok
 *  *   test: graph endpoint returns nodes and edges
 */

import assert from "node:assert/strict";
import test from "node:test";

import request from "supertest";

import { makeApp, fakeRecord } from "./helpers.js";

test("GET /health returns ok", async () => {
  const { app } = await makeApp();
  const response = await request(app).get("/health");
  assert.equal(response.status, 200);
  assert.deepEqual(response.body, { status: "ok" });
});

test("GET /api/graph returns nodes and edges", async () => {
  const { app } = await makeApp({
    "MATCH (n:Entity)": [fakeRecord("Alice", "founded", "Acme")],
  });
  const response = await request(app).get("/api/graph");
  assert.equal(response.status, 200);
  assert.equal(response.body.nodes.length, 2);
  assert.equal(response.body.edges.length, 1);
  assert.equal(response.body.edges[0].predicate, "founded");
});
