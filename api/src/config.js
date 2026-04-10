#!/usr/bin/env node
/**
 * config.js --- environment configuration for the BFF
 *  *
 *  * Contains:
 *  *   DEFAULTS: fallback configuration values
 */

const DEFAULTS = {
  port: 4000,
  neo4jUri: "bolt://localhost:7687",
  neo4jUser: "neo4j",
  neo4jPassword: "graphmind-dev",
  neo4jDatabase: "neo4j",
  corsOrigin: "http://localhost:5173",
};
