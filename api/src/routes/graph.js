#!/usr/bin/env node
/**
 * graph.js --- graph read endpoints backing the viewer
 *  *
 *  * Contains:
 *  *   imports + router factory
 *  *   GRAPH_QUERY: nodes and relationships for the viewer
 *  *   toViewGraph(): maps records into viewer-friendly JSON
 *  *   parseLimit(): validates the limit query parameter
 *  *   graphRouter(): serves the graph JSON endpoint
 *  *   LABELS_QUERY + labels endpoint
 *  *   NODE_QUERY: single-node neighborhood read
 *  *   mountNodeEndpoint(): node detail neighborhood endpoint
 */

import { Router } from "express";

import { runQuery } from "../neo4jClient.js";

const GRAPH_QUERY = `
MATCH (n:Entity)
OPTIONAL MATCH (n)-[r:RELATED]->(m:Entity)
RETURN n, r, m
LIMIT $limit
`.trim();

/**
 * Maps raw Neo4j records into the viewer's node/edge JSON shape.
 *
 * @param records - Raw records from GRAPH_QUERY.
 * @returns graph - { nodes, edges } payload for the viewer.
 */
export function toViewGraph(records) {
  const nodes = new Map();
  const edges = new Map();
  for (const record of records) {
    const source = record.get("n");
    const target = record.get("m");
    const relationship = record.get("r");
    if (source) {
      nodes.set(source.properties.name, {
        id: source.properties.name,
        label: source.properties.name,
        type: source.properties.entity_type ?? "CONCEPT",
      });
    }
    if (target) {
      nodes.set(target.properties.name, {
        id: target.properties.name,
        label: target.properties.name,
        type: target.properties.entity_type ?? "CONCEPT",
      });
    }
    if (source && target && relationship) {
      const edgeId = `${source.properties.name}|${relationship.properties.predicate}|${target.properties.name}`;
      edges.set(edgeId, {
        id: edgeId,
        source: source.properties.name,
        target: target.properties.name,
        predicate: relationship.properties.predicate,
        confidence: relationship.properties.confidence ?? null,
        inferred: relationship.properties.inferred ?? false,
      });
    }
  }
  return { nodes: [...nodes.values()], edges: [...edges.values()] };
}

/**
 * Validates the limit query parameter, clamping to a safe range.
 *
 * @param raw - Raw query string value.
 * @returns limit - Integer between 1 and 5000, default 500.
 */
export function parseLimit(raw) {
  const parsed = Number.parseInt(raw ?? "", 10);
  if (Number.isNaN(parsed)) {
    return 500;
  }
  return Math.min(Math.max(parsed, 1), 5000);
}

/**
 * Builds the router serving graph JSON to the viewer.
 *
 * @param driver - Neo4j driver instance.
 * @param config - Resolved service configuration.
 * @returns router - Express router with the graph endpoint mounted.
 */
export function graphRouter(driver, config) {
  const router = Router();

  router.get("/graph", async (request, response, next) => {
    try {
      const limit = parseLimit(request.query.limit);
      const records = await runQuery(driver, GRAPH_QUERY, { limit }, config.neo4jDatabase);
      response.json(toViewGraph(records));
    } catch (error) {
      next(error);
    }
  });

  return router;
}

const LABELS_QUERY = `
MATCH (n:Entity)
RETURN DISTINCT n.entity_type AS type, count(*) AS count
ORDER BY count DESC
`.trim();

/**
 * Mounts an endpoint listing entity types with counts.
 *
 * @param router - Router to extend.
 * @param driver - Neo4j driver instance.
 * @param config - Resolved service configuration.
 */
export function mountLabelsEndpoint(router, driver, config) {
  router.get("/graph/labels", async (_request, response, next) => {
    try {
      const records = await runQuery(driver, LABELS_QUERY, {}, config.neo4jDatabase);
      response.json(
        records.map((record) => ({
          type: record.get("type") ?? "CONCEPT",
          count: record.get("count").toNumber(),
        })),
      );
    } catch (error) {
      next(error);
    }
  });
}

const NODE_QUERY = `
MATCH (n:Entity {name: $name})
OPTIONAL MATCH (n)-[r:RELATED]-(m:Entity)
RETURN n, r, m
LIMIT 200
`.trim();

/**
 * Mounts an endpoint returning one node's neighborhood for the detail panel.
 *
 * @param router - Router to extend.
 * @param driver - Neo4j driver instance.
 * @param config - Resolved service configuration.
 */
export function mountNodeEndpoint(router, driver, config) {
  router.get("/graph/node/:name", async (request, response, next) => {
    try {
      const records = await runQuery(
        driver,
        NODE_QUERY,
        { name: request.params.name },
        config.neo4jDatabase,
      );
      if (records.length === 0) {
        response.status(404).json({ error: `unknown entity: ${request.params.name}` });
        return;
      }
      response.json(toViewGraph(records));
    } catch (error) {
      next(error);
    }
  });
}
