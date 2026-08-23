#!/usr/bin/env node
/**
 * app.js --- express application factory wiring middleware and routers
 *  *
 *  * Contains:
 *  *   createApp(): builds the configured express app
 *  *   corsMiddleware(): minimal CORS headers for the viewer origin
 *  *   mountHealthEndpoint(): liveness probe route
 */

import express from "express";

import { errorHandler, notFoundHandler } from "./middleware/errorHandler.js";
import { exportGraphmlRouter } from "./routes/exportGraphml.js";
import { graphRouter, mountLabelsEndpoint, mountNodeEndpoint } from "./routes/graph.js";
import { metricsRouter, mountHubsEndpoint } from "./routes/metrics.js";

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
  const graph = graphRouter(driver, config);
  mountLabelsEndpoint(graph, driver, config);
  mountNodeEndpoint(graph, driver, config);
  app.use("/api", graph);
  app.use("/api", exportGraphmlRouter(driver, config));
  const metrics = metricsRouter(driver, config);
  mountHubsEndpoint(metrics, driver, config);
  app.use("/api", metrics);
  app.use(notFoundHandler);
  app.use(errorHandler);
  return app;
}

/**
 * Builds minimal CORS middleware allowing the viewer origin.
 *
 * @param origin - Allowed origin for cross-origin viewer requests.
 * @returns middleware - Express middleware setting CORS headers.
 */
export function corsMiddleware(origin) {
  return (request, response, next) => {
    response.setHeader("Access-Control-Allow-Origin", origin);
    response.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
    response.setHeader("Access-Control-Allow-Headers", "Content-Type");
    if (request.method === "OPTIONS") {
      response.status(204).end();
      return;
    }
    next();
  };
}

/**
 * Mounts the liveness probe route used by compose healthchecks.
 *
 * @param app - Express application instance.
 */
export function mountHealthEndpoint(app) {
  app.get("/health", (_request, response) => {
    response.json({ status: "ok" });
  });
}
