#!/usr/bin/env node
/**
 * useGraphFilter.js --- hook filtering the visible graph by search text
 *  *
 *  * Contains:
 *  *   useGraphFilter(): filters nodes and their induced edges
 *  *   useDebouncedValue(): debounces fast-changing input
 *  *   useTypeFilter(): toggles visibility per entity type
 *  *   useRegexMode(): tracks the substring/regex toggle state
 *  *   useRegexFilter(): filters nodes by a compiled pattern
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

/**
 * Tracks which entity types are currently visible in the viewer.
 *
 * @param initialTypes - Types visible initially.
 * @returns state - { hidden, toggleType, isVisible } type filter state.
 */
export function useTypeFilter(initialTypes = []) {
  const [hidden, setHidden] = useState(new Set());
  const toggleType = (type) => {
    setHidden((current) => {
      const next = new Set(current);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };
  const isVisible = (type) => !hidden.has(type);
  return { hidden, toggleType, isVisible, initialTypes };
}

/**
 * Tracks whether the search filter is in regex mode.
 *
 * @returns state - { regexMode, toggleRegexMode } toggle state.
 */
export function useRegexMode() {
  const [regexMode, setRegexMode] = useState(false);
  const toggleRegexMode = () => setRegexMode((current) => !current);
  return { regexMode, toggleRegexMode };
}

/**
 * Filters a view graph using a compiled regular expression.
 *
 * @param graph - Full { nodes, edges } payload.
 * @param pattern - Compiled RegExp, or null for no filtering.
 * @returns filtered - Graph limited to matching nodes and induced edges.
 */
export function useRegexFilter(graph, pattern) {
  return useMemo(() => {
    if (!pattern) {
      return graph;
    }
    const nodes = graph.nodes.filter((node) => pattern.test(node.label) || pattern.test(node.type));
    const visible = new Set(nodes.map((node) => node.id));
    const edges = graph.edges.filter((edge) => visible.has(edge.source) && visible.has(edge.target));
    return { nodes, edges };
  }, [graph, pattern]);
}
