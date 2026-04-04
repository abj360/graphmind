#!/usr/bin/env node
/**
 * MetricsDashboard.jsx --- dashboard panel showing node/edge dedup metrics
 *  *
 *  * Contains:
 *  *   MetricsDashboard: dedup metrics panel
 */

import { useEffect, useState } from "react";

import { fetchDedupMetrics } from "../apiClient.js";

/**
 * Renders the node/edge dedup metrics dashboard panel.
 *
 * @returns element - Metrics panel with totals and duplicate clusters.
 */
export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchDedupMetrics()
      .then((payload) => {
        if (!cancelled) {
          setMetrics(payload);
        }
      })
      .catch((fetchError) => {
        if (!cancelled) {
          setError(fetchError.message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <div className="metrics-panel metrics-error">metrics unavailable</div>;
  }
  if (!metrics) {
    return <div className="metrics-panel">loading metrics…</div>;
  }
  return (
    <div className="metrics-panel">
      <h2>graph metrics</h2>
      <dl className="metrics-grid">
        <dt>nodes</dt>
        <dd>{metrics.nodes.total}</dd>
        <dt>edges</dt>
        <dd>{metrics.edges.total}</dd>
        <dt>predicates</dt>
        <dd>{metrics.edges.distinctPredicates}</dd>
        <dt>mean conf</dt>
        <dd>{formatConfidence(metrics.edges.meanConfidence)}</dd>
        <dt>dup clusters</dt>
        <dd>{metrics.duplicates.clusters}</dd>
      </dl>
      <DuplicateExamples examples={metrics.duplicates.examples} />
    </div>
  );
}
