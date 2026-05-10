#!/usr/bin/env node
/**
 * useGraphFilter.js --- hook filtering the visible graph by search text
 *  *
 *  * Contains:
 *  *   useGraphFilter(): filters nodes and their induced edges
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
