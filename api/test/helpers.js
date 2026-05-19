#!/usr/bin/env node
/**
 * helpers.js --- shared test doubles and fixtures for BFF contract tests
 *  *
 *  * Contains:
 *  *   fakeConfig(): deterministic test configuration
 *  *   fakeRecord(): builds a raw-record shaped double
 *  *   stubDriver(): driver double serving canned records
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
  return {
    calls: [],
    session({ database } = {}) {
      return {
        run: async (query, params) => {
          const entry = Object.entries(resultsByQuery).find(([fragment]) =>
            query.includes(fragment),
          );
          const records = entry ? entry[1] : [];
          const driver = resultsByQuery.__driver;
          if (driver) {
            driver.calls.push({ query, params, database });
          }
          return { records };
        },
        close: async () => {},
      };
    },
    close: async () => {},
  };
}
