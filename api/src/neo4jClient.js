#!/usr/bin/env node
/**
 * neo4jClient.js --- thin Neo4j driver wrapper used by the route handlers
 *  *
 *  * Contains:
 *  *   createDriver(): builds the shared driver
 *  *   runQuery(): executes a read query and unwraps records
 *  *   closeDriver(): releases the shared driver
 *  *   verifyConnectivity(): fails fast when Neo4j is down
 *  *   runQueries(): executes several queries sequentially
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

/**
 * Executes one read query and unwraps the raw records.
 *
 * @param driver - Neo4j driver instance.
 * @param query - Cypher statement to run.
 * @param params - Query parameters.
 * @param database - Target database name.
 * @returns records - Raw Neo4j record objects.
 */
export async function runQuery(driver, query, params = {}, database = "neo4j") {
  const session = driver.session({ database });
  try {
    const result = await session.run(query, params);
    return result.records;
  } finally {
    await session.close();
  }
}

/**
 * Releases the shared Neo4j driver, tolerating repeated calls.
 *
 * @param driver - Neo4j driver instance to close.
 */
export async function closeDriver(driver) {
  if (driver) {
    await driver.close();
  }
}

/**
 * Verifies Neo4j connectivity, failing fast when unreachable.
 *
 * @param driver - Neo4j driver instance.
 * @returns ok - True when the instance answers a trivial query.
 */
export async function verifyConnectivity(driver) {
  try {
    await driver.verifyConnectivity();
    return true;
  } catch (error) {
    throw new Error(`neo4j unreachable: ${error.message}`);
  }
}

/**
 * Executes several queries sequentially, collecting their records.
 *
 * @param driver - Neo4j driver instance.
 * @param queries - Cypher statements to run in order.
 * @param database - Target database name.
 * @returns results - One record list per query, in order.
 */
export async function runQueries(driver, queries, database = "neo4j") {
  const results = [];
  for (const query of queries) {
    results.push(await runQuery(driver, query, {}, database));
  }
  return results;
}
