#!/usr/bin/env node
/**
 * exportGraphml.js --- GraphML export endpoint for downstream graph tooling
 *  *
 *  * Contains:
 *  *   EXPORT_QUERY: full-graph read for export
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
