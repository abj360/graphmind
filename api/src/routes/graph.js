#!/usr/bin/env node
/**
 * graph.js --- graph read endpoints backing the viewer
 *  *
 *  * Contains:
 *  *   imports + router factory
 *  *   GRAPH_QUERY: nodes and relationships for the viewer
 *  *   toViewGraph(): maps records into viewer-friendly JSON
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
