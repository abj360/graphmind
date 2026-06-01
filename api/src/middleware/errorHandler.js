#!/usr/bin/env node
/**
 * errorHandler.js --- central error-handling middleware for the BFF
 *  *
 *  * Contains:
 *  *   errorHandler(): maps errors to JSON responses
 *  *   notFoundHandler(): JSON 404 for unmatched routes
 */

/**
 * Maps thrown errors to consistent JSON error responses.
 *
 * @param error - Error thrown by a route handler.
 * @param _request - Express request, unused.
 * @param response - Express response used to send the error payload.
 * @param _next - Express next callback, unused.
 */
export function errorHandler(error, _request, response, _next) {
  const status = error.statusCode ?? 500;
  const payload = { error: error.message ?? "internal server error" };
  if (status >= 500) {
    console.error("unhandled route error:", error);
  }
  response.status(status).json(payload);
}

/**
 * Responds with a JSON 404 for unmatched routes.
 *
 * @param request - Express request that matched nothing.
 * @param response - Express response used to send the 404 payload.
 */
export function notFoundHandler(request, response) {
  response.status(404).json({ error: `no such route: ${request.method} ${request.path}` });
}
