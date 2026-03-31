#!/usr/bin/env node
/**
 * index.js --- service entrypoint: boots the BFF HTTP server
 *  *
 *  * Contains:
 *  *   main(): boots the HTTP server
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
