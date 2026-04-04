#!/usr/bin/env node
/**
 * app.js --- express application factory wiring middleware and routers
 *  *
 *  * Contains:
 *  *   createApp(): builds the configured express app
 */

import express from "express";

import { errorHandler, notFoundHandler } from "./middleware/errorHandler.js";
import { exportGraphmlRouter } from "./routes/exportGraphml.js";
import { graphRouter } from "./routes/graph.js";
import { metricsRouter } from "./routes/metrics.js";

/**
 * Builds the configured Express application for the BFF.
 *
 * @param driver - Neo4j driver instance.
 * @param config - Resolved service configuration.
 * @returns app - Configured Express application.
 */
export function createApp(driver, config) {
  const app = express();
  app.use(express.json());
  app.use(corsMiddleware(config.corsOrigin));
  mountHealthEndpoint(app);
  app.use("/api", graphRouter(driver, config));
  app.use("/api", exportGraphmlRouter(driver, config));
  app.use("/api", metricsRouter(driver, config));
  app.use(notFoundHandler);
  app.use(errorHandler);
  return app;
}
