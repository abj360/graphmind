#!/usr/bin/env node
/**
 * App.jsx --- root component composing viewer, controls, and panels
 *  *
 *  * Contains:
 *  *   App: composition root of the viewer
 */

import { useEffect, useState } from "react";

import { fetchGraph } from "./apiClient.js";
import GraphViewer from "./components/GraphViewer.jsx";
import SearchBar from "./components/SearchBar.jsx";
import { useGraphFilter } from "./hooks/useGraphFilter.js";

/**
 * Composes the graph viewer with search controls.
 *
 * @returns element - Root application layout.
 */
export default function App() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const { query, setQuery, filtered } = useGraphFilter(graph);

  useEffect(() => {
    let cancelled = false;
    fetchGraph()
      .then((payload) => {
        if (!cancelled) {
          setGraph(payload);
          setLoading(false);
        }
      })
      .catch((fetchError) => {
        if (!cancelled) {
          setError(fetchError.message);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <div className="app-status app-error">failed to load graph: {error}</div>;
  }
  if (loading) {
    return <div className="app-status">loading graph…</div>;
  }
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>graphmind</h1>
        <SearchBar query={query} onChange={setQuery} />
      </header>
      <main className="app-main">
        <section className="app-canvas">
          <GraphViewer graph={filtered} />
        </section>
      </main>
    </div>
  );
}
