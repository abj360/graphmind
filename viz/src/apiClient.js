#!/usr/bin/env node
/**
 * apiClient.js --- typed fetch wrappers for the BFF endpoints
 *  *
 *  * Contains:
 *  *   API_BASE: resolved API base URL
 *  *   fetchJson(): GET helper with error unwrapping
 *  *   fetchGraph(): loads the view graph
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

/**
 * Fetches JSON from a BFF endpoint, unwrapping error payloads.
 *
 * @param path - Endpoint path relative to the API base.
 * @returns payload - Parsed JSON response body.
 */
async function fetchJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.error ?? detail;
    } catch {
      // error payload was not JSON; keep the HTTP status detail
    }
    throw new Error(`api request failed: ${detail}`);
  }
  return response.json();
}

/**
 * Loads the view graph from the BFF.
 *
 * @param limit - Maximum records to fetch.
 * @returns graph - { nodes, edges } payload for the viewer.
 */
export function fetchGraph(limit = 500) {
  return fetchJson(`/api/graph?limit=${limit}`);
}
