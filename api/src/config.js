#!/usr/bin/env node
/**
 * config.js --- environment configuration for the BFF
 *  *
 *  * Contains:
 *  *   DEFAULTS: fallback configuration values
 *  *   loadConfig(): reads configuration from the environment
 *  *   validateConfig(): rejects unusable configuration
 *  *   describeConfig(): redacted one-line config summary
 */

const DEFAULTS = {
  port: 4000,
  neo4jUri: "bolt://localhost:7687",
  neo4jUser: "neo4j",
  neo4jPassword: "graphmind-dev",
  neo4jDatabase: "neo4j",
  corsOrigin: "http://localhost:5173",
};

/**
 * Reads service configuration from environment variables.
 *
 * @param env - Environment mapping to read; defaults to process.env.
 * @returns config - Resolved configuration with overrides applied.
 */
export function loadConfig(env = process.env) {
  return {
    port: Number.parseInt(env.API_PORT ?? "", 10) || DEFAULTS.port,
    neo4jUri: env.NEO4J_URI ?? DEFAULTS.neo4jUri,
    neo4jUser: env.NEO4J_USER ?? DEFAULTS.neo4jUser,
    neo4jPassword: env.NEO4J_PASSWORD ?? DEFAULTS.neo4jPassword,
    neo4jDatabase: env.NEO4J_DATABASE ?? DEFAULTS.neo4jDatabase,
    corsOrigin: env.API_CORS_ORIGIN ?? DEFAULTS.corsOrigin,
  };
}

/**
 * Rejects configuration values the service cannot start with.
 *
 * @param config - Configuration produced by loadConfig().
 * @returns config - The same configuration, if valid.
 */
export function validateConfig(config) {
  if (!Number.isInteger(config.port) || config.port <= 0) {
    throw new Error(`invalid API port: ${config.port}`);
  }
  if (!config.neo4jUri.startsWith("bolt")) {
    throw new Error(`NEO4J_URI must use the bolt scheme: ${config.neo4jUri}`);
  }
  return config;
}

/**
 * Renders a one-line config summary with the password redacted.
 *
 * @param config - Resolved service configuration.
 * @returns summary - Log-friendly config description, password masked.
 */
export function describeConfig(config) {
  return (
    `port=${config.port} neo4j=${config.neo4jUri} user=${config.neo4jUser} ` +
    `password=*** db=${config.neo4jDatabase} cors=${config.corsOrigin}`
  );
}
