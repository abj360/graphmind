#!/usr/bin/env node
/**
 * App.jsx --- root component composing viewer, controls, and panels
 *  *
 *  * Contains:
 *  *   App: composition root of the viewer
 */

import { useCallback, useEffect, useState } from "react";

import { fetchGraph } from "./apiClient.js";
import GraphLegend from "./components/GraphLegend.jsx";
import GraphViewer from "./components/GraphViewer.jsx";
import MetricsDashboard from "./components/MetricsDashboard.jsx";
import NodeDetailPanel from "./components/NodeDetailPanel.jsx";
import SearchBar from "./components/SearchBar.jsx";
import { useGraphFilter } from "./hooks/useGraphFilter.js";

/**
 * Composes the graph viewer with search, legend, metrics, and detail panel.
 *
 * @returns element - Root application layout.
 */
export default function App() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
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

  const handleSelect = useCallback((node) => setSelectedNode(node), []);
  const handleClosePanel = useCallback(() => setSelectedNode(null), []);

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
          <GraphViewer graph={filtered} onSelectNode={handleSelect} />
          <GraphLegend nodes={graph.nodes} />
        </section>
        <aside className="app-sidebar">
          <MetricsDashboard />
          <NodeDetailPanel node={selectedNode} edges={graph.edges} onClose={handleClosePanel} />
        </aside>
      </main>
    </div>
  );
}
