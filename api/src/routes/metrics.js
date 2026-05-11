#!/usr/bin/env node
/**
 * metrics.js --- dedup and graph-shape metrics for the dashboard
 *  *
 *  * Contains:
 *  *   NODE_STATS_QUERY: node counts by entity type
 *  *   EDGE_STATS_QUERY: edge counts and predicate spread
 *  *   DUPLICATE_CANDIDATES_QUERY: same-name entity clusters
 *  *   toNumber(): unwraps neo4j integer values
 *  *   buildMetricsPayload(): shapes the dashboard payload
 */

import { Router } from "express";

import { runQuery } from "../neo4jClient.js";

const NODE_STATS_QUERY = `
MATCH (n:Entity)
RETURN count(n) AS total, collect(DISTINCT n.entity_type) AS types
`.trim();

const EDGE_STATS_QUERY = `
MATCH ()-[r:RELATED]->()
RETURN count(r) AS total, count(DISTINCT r.predicate) AS predicates,
       avg(r.confidence) AS meanConfidence
`.trim();

const DUPLICATE_CANDIDATES_QUERY = `
MATCH (n:Entity)
WITH toLower(n.name) AS folded, collect(n.name) AS variants
WHERE size(variants) > 1
RETURN folded, variants
LIMIT 100
`.trim();

/**
 * Unwraps a Neo4j integer value into a plain number.
 *
 * @param value - Neo4j Integer or plain number.
 * @returns unwrapped - Plain JavaScript number.
 */
function toNumber(value) {
  if (value === null || value === undefined) {
    return 0;
  }
  return typeof value.toNumber === "function" ? value.toNumber() : Number(value);
}

/**
 * Shapes raw query results into the dashboard metrics payload.
 *
 * @param nodeRecord - Record from NODE_STATS_QUERY.
 * @param edgeRecord - Record from EDGE_STATS_QUERY.
 * @param duplicateRecords - Records from DUPLICATE_CANDIDATES_QUERY.
 * @returns payload - Metrics JSON served to the dashboard.
 */
export function buildMetricsPayload(nodeRecord, edgeRecord, duplicateRecords) {
  const duplicates = duplicateRecords.map((record) => ({
    folded: record.get("folded"),
    variants: record.get("variants"),
  }));
  return {
    nodes: { total: toNumber(nodeRecord?.get("total")), types: nodeRecord?.get("types") ?? [] },
    edges: {
      total: toNumber(edgeRecord?.get("total")),
      distinctPredicates: toNumber(edgeRecord?.get("predicates")),
      meanConfidence: edgeRecord?.get("meanConfidence") ?? null,
    },
    duplicates: {
      clusters: duplicates.length,
      examples: duplicates.slice(0, 10),
    },
  };
}
