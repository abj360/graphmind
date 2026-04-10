#!/usr/bin/env node
/**
 * index.js --- service entrypoint: boots the BFF HTTP server
 *  *
 *  * Contains:
 *  *   main(): boots the HTTP server
 *  *   registerShutdown(): graceful SIGTERM/SIGINT handling
 *  *   entrypoint invocation
 */

import { createApp } from "./app.js";
import { loadConfig, validateConfig } from "./config.js";
import { closeDriver, createDriver, verifyConnectivity } from "./neo4jClient.js";

/**
 * Boots the BFF HTTP server with validated configuration.
 */
async function main() {
  const config = validateConfig(loadConfig());
  const driver = createDriver(config);
  await verifyConnectivity(driver);
  const app = createApp(driver, config);
  const server = app.listen(config.port, () => {
    console.log(`graphmind-api listening on :${config.port}`);
  });
  registerShutdown(server, driver);
}

/**
 * Registers graceful shutdown handlers on the HTTP server.
 *
 * @param server - Listening HTTP server.
 * @param driver - Neo4j driver to close on shutdown.
 */
function registerShutdown(server, driver) {
  const shutdown = async (signal) => {
    console.log(`received ${signal}; shutting down`);
    server.close(async () => {
      await closeDriver(driver);
      process.exit(0);
    });
  };
  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

main().catch((error) => {
  console.error("fatal startup error:", error);
  process.exit(1);
});
