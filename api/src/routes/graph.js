#!/usr/bin/env node
/**
 * graph.js --- graph read endpoints backing the viewer
 *  *
 *  * Contains:
 *  *   imports + router factory
 *  *   GRAPH_QUERY: nodes and relationships for the viewer
 */

import { Router } from "express";

import { runQuery } from "../neo4jClient.js";

const GRAPH_QUERY = `
MATCH (n:Entity)
OPTIONAL MATCH (n)-[r:RELATED]->(m:Entity)
RETURN n, r, m
LIMIT $limit
`.trim();
