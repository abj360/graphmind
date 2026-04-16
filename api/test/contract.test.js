#!/usr/bin/env node
/**
 * contract.test.js --- contract tests for the BFF HTTP endpoints
 *  *
 *  * Contains:
 *  *   test: health endpoint returns ok
 *  *   test: graph endpoint returns nodes and edges
 *  *   test: graph endpoint dedupes repeated nodes
 *  *   test: graph endpoint honors the limit parameter
 *  *   test: limit parameter is clamped to range
 *  *   test: labels endpoint lists entity types
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

test("GET /api/graph dedupes repeated nodes", async () => {
  const { app } = await makeApp({
    "MATCH (n:Entity)": [
      fakeRecord("Alice", "founded", "Acme"),
      fakeRecord("Bob", "joined", "Acme"),
    ],
  });
  const response = await request(app).get("/api/graph");
  assert.equal(response.body.nodes.length, 3);
});

test("GET /api/graph passes a parsed limit to the query", async () => {
  const { app, driver } = await makeApp({ "MATCH (n:Entity)": [] });
  await request(app).get("/api/graph?limit=50");
  const call = driver.calls.find((entry) => entry.params.limit);
  assert.equal(call.params.limit, 50);
});

test("GET /api/graph clamps an excessive limit", async () => {
  const { app, driver } = await makeApp({ "MATCH (n:Entity)": [] });
  await request(app).get("/api/graph?limit=999999");
  const call = driver.calls.find((entry) => entry.params.limit);
  assert.equal(call.params.limit, 5000);
});

test("GET /api/graph/labels lists entity types with counts", async () => {
  const { app } = await makeApp({
    "RETURN DISTINCT n.entity_type": [
      { get: (key) => (key === "type" ? "ORG" : { toNumber: () => 4 }) },
    ],
  });
  const response = await request(app).get("/api/graph/labels");
  assert.equal(response.status, 200);
  assert.deepEqual(response.body, [{ type: "ORG", count: 4 }]);
});
