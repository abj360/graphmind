#!/usr/bin/env node
/**
 * exportGraphml.js --- GraphML export endpoint for downstream graph tooling
 *  *
 *  * Contains:
 *  *   EXPORT_QUERY: full-graph read for export
 *  *   GRAPHML_CONTENT_TYPE: response media type
 *  *   exportFilename(): builds a dated download filename
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
