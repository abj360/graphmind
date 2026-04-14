#!/usr/bin/env node
/**
 * MetricsDashboard.jsx --- dashboard panel showing node/edge dedup metrics
 *  *
 *  * Contains:
 *  *   MetricsDashboard: dedup metrics panel
 *  *   DuplicateExamples: lists sample duplicate clusters
 *  *   formatConfidence(): renders mean confidence for display
 *  *   MetricsRow: one label/value row in the grid
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

/**
 * Lists a few duplicate-name clusters for reviewer attention.
 *
 * @param props.examples - Duplicate cluster examples from the payload.
 * @returns element - Compact list of variant groups.
 */
function DuplicateExamples({ examples }) {
  if (!examples || examples.length === 0) {
    return <p className="metrics-note">no duplicate-name clusters</p>;
  }
  return (
    <ul className="metrics-duplicates">
      {examples.map((cluster) => (
        <li key={cluster.folded}>
          {cluster.variants.join(" / ")}
        </li>
      ))}
    </ul>
  );
}

/**
 * Formats a mean confidence score for compact display.
 *
 * @param value - Mean confidence between 0 and 1, possibly null.
 * @returns text - Two-decimal rendering, or an em dash when absent.
 */
export function formatConfidence(value) {
  if (typeof value !== "number") {
    return "—";
  }
  return value.toFixed(2);
}

/**
 * Renders one label/value row in the metrics grid.
 *
 * @param props.label - Metric label.
 * @param props.value - Preformatted metric value.
 * @returns element - Grid row fragments for the metric.
 */
export function MetricsRow({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}
