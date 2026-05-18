#!/usr/bin/env node
/**
 * useGraphFilter.js --- hook filtering the visible graph by search text
 *  *
 *  * Contains:
 *  *   useGraphFilter(): filters nodes and their induced edges
 *  *   useDebouncedValue(): debounces fast-changing input
 */

import { useEffect, useMemo, useState } from "react";

import { matchesQuery, normalizeQuery } from "../components/SearchBar.jsx";

/**
 * Filters a view graph to nodes matching a query and their induced edges.
 *
 * @param graph - Full { nodes, edges } payload.
 * @returns state - { query, setQuery, filtered } filter state and result.
 */
export function useGraphFilter(graph) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const normalized = normalizeQuery(query);
    if (!normalized) {
      return graph;
    }
    const nodes = graph.nodes.filter((node) => matchesQuery(node, normalized));
    const visible = new Set(nodes.map((node) => node.id));
    const edges = graph.edges.filter((edge) => visible.has(edge.source) && visible.has(edge.target));
    return { nodes, edges };
  }, [graph, query]);
  return { query, setQuery, filtered };
}

/**
 * Debounces a fast-changing value to avoid re-filtering every keystroke.
 *
 * @param value - Value to debounce.
 * @param delayMs - Quiet period before the value settles.
 * @returns debounced - Value updated only after the quiet period.
 */
export function useDebouncedValue(value, delayMs = 150) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(handle);
  }, [value, delayMs]);
  return debounced;
}
