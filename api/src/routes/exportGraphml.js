#!/usr/bin/env node
/**
 * exportGraphml.js --- GraphML export endpoint for downstream graph tooling
 *  *
 *  * Contains:
 *  *   EXPORT_QUERY: full-graph read for export
 *  *   GRAPHML_CONTENT_TYPE: response media type
 *  *   exportFilename(): builds a dated download filename
 *  *   exportGraphmlRouter(): serves the GraphML export
 */

import { Router } from "express";

import { runQuery } from "../neo4jClient.js";
import { toViewGraph, parseLimit } from "./graph.js";
import { graphStats, toGraphML, validateGraphInput } from "../graphml/serializer.js";

const EXPORT_QUERY = `
MATCH (n:Entity)
OPTIONAL MATCH (n)-[r:RELATED]->(m:Entity)
RETURN n, r, m
LIMIT $limit
`.trim();

const GRAPHML_CONTENT_TYPE = "application/graphml+xml; charset=utf-8";

/**
 * Builds a dated GraphML download filename.
 *
 * @param now - Current time; injectable for tests.
 * @returns filename - Dated .graphml filename.
 */
export function exportFilename(now = new Date()) {
  const stamp = now.toISOString().slice(0, 10);
  return `graphmind-${stamp}.graphml`;
}

/**
 * Builds the router serving GraphML exports of the whole graph.
 *
 * @param driver - Neo4j driver instance.
 * @param config - Resolved service configuration.
 * @returns router - Express router with the export endpoint mounted.
 */
export function exportGraphmlRouter(driver, config) {
  const router = Router();

  router.get("/export/graphml", async (request, response, next) => {
    try {
      const limit = parseLimit(request.query.limit);
      const records = await runQuery(driver, EXPORT_QUERY, { limit }, config.neo4jDatabase);
      const graph = validateGraphInput(toViewGraph(records));
      response
        .setHeader("Content-Type", GRAPHML_CONTENT_TYPE)
        .setHeader("Content-Disposition", `attachment; filename="${exportFilename()}"`)
        .send(toGraphML(graph));
    } catch (error) {
      next(error);
    }
  });

  return router;
}
