#!/usr/bin/env node
/**
 * helpers.js --- shared test doubles and fixtures for BFF contract tests
 *  *
 *  * Contains:
 *  *   fakeConfig(): deterministic test configuration
 *  *   fakeRecord(): builds a raw-record shaped double
 *  *   stubDriver(): driver double serving canned records
 *  *   makeApp(): wires the app with a stub driver
 *  *   metricsRecords(): canned metrics query records
 */

/**
 * Builds a deterministic service configuration for tests.
 *
 * @returns config - Resolved configuration with test values.
 */
export function fakeConfig() {
  return {
    port: 0,
    neo4jUri: "bolt://localhost:7687",
    neo4jUser: "neo4j",
    neo4jPassword: "test",
    neo4jDatabase: "neo4j",
    corsOrigin: "http://localhost:5173",
  };
}

/**
 * Builds a raw Neo4j record shaped double for one triple.
 *
 * @param subject - Subject node name.
 * @param predicate - Relationship predicate.
 * @param object - Object node name.
 * @param extra - Extra relationship properties to merge in.
 * @returns record - Record double responding to get().
 */
export function fakeRecord(subject, predicate, object, extra = {}) {
  const node = (name) => ({
    properties: { name, entity_type: extra[`${name}_type`] ?? "CONCEPT" },
  });
  const values = {
    n: subject ? node(subject) : null,
    m: object ? node(object) : null,
    r: predicate
      ? { properties: { predicate, confidence: extra.confidence ?? 0.9, inferred: false } }
      : null,
  };
  return { get: (key) => values[key] ?? null };
}

/**
 * Builds a Neo4j driver double that serves canned query results.
 *
 * @param resultsByQuery - Map of query-substring to records to return.
 * @returns driver - Double with session() and close() implemented.
 */
export function stubDriver(resultsByQuery = {}) {
  const calls = [];
  return {
    calls,
    session({ database } = {}) {
      return {
        run: async (query, params) => {
          calls.push({ query, params, database });
          const entry = Object.entries(resultsByQuery).find(([fragment]) =>
            query.includes(fragment),
          );
          return { records: entry ? entry[1] : [] };
        },
        close: async () => {},
      };
    },
    close: async () => {},
  };
}

/**
 * Wires the Express app with a stub driver and canned records.
 *
 * @param resultsByQuery - Map of query-substring to records to return.
 * @returns app - Express application ready for supertest.
 */
export async function makeApp(resultsByQuery = {}) {
  const { createApp } = await import("../src/app.js");
  const driver = stubDriver(resultsByQuery);
  return { app: createApp(driver, fakeConfig()), driver };
}

/**
 * Builds canned records for the metrics endpoint queries.
 *
 * @returns resultsByQuery - Map of query fragments to canned records.
 */
export function metricsRecords() {
  return {
    "count(n) AS total": [
      { get: (key) => (key === "total" ? { toNumber: () => 7 } : ["ORG", "PERSON"]) },
    ],
    "count(r) AS total": [
      {
        get: (key) =>
          ({ total: { toNumber: () => 9 }, predicates: { toNumber: () => 4 }, meanConfidence: 0.77 })[
            key
          ],
      },
    ],
    "toLower(n.name) AS folded": [],
  };
}
