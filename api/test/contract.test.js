#!/usr/bin/env node
/**
 * contract.test.js --- contract tests for the BFF HTTP endpoints
 *  *
 *  * Contains:
 *  *   test: health endpoint returns ok
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
