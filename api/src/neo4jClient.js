#!/usr/bin/env node
/**
 * neo4jClient.js --- thin Neo4j driver wrapper used by the route handlers
 *  *
 *  * Contains:
 *  *   createDriver(): builds the shared driver
 */

import neo4j from "neo4j-driver";

/**
 * Builds the shared Neo4j driver from service configuration.
 *
 * @param config - Resolved service configuration.
 * @returns driver - Connected Neo4j driver instance.
 */
export function createDriver(config) {
  return neo4j.driver(config.neo4jUri, neo4j.auth.basic(config.neo4jUser, config.neo4jPassword));
}
