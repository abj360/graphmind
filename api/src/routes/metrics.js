#!/usr/bin/env node
/**
 * metrics.js --- dedup and graph-shape metrics for the dashboard
 *  *
 *  * Contains:
 *  *   NODE_STATS_QUERY: node counts by entity type
 */

import { Router } from "express";

import { runQuery } from "../neo4jClient.js";

const NODE_STATS_QUERY = `
MATCH (n:Entity)
RETURN count(n) AS total, collect(DISTINCT n.entity_type) AS types
`.trim();
