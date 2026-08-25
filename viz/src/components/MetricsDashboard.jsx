/**
 * MetricsDashboard.jsx --- dashboard panel showing node/edge dedup metrics
 *  *
 *  * Contains:
 *  *   MetricsDashboard: dedup metrics panel
 *  *   DuplicateExamples: lists sample duplicate clusters
 *  *   formatConfidence(): renders mean confidence for display
 *  *   MetricsRow: one label/value row in the grid
 *  *   refreshInterval(): poll cadence for live metrics
 *  *   RefreshButton: manual metrics refresh control
 *  *   useMetricsRefresh(): polling refresh for the metrics panel
 *  *   MetricsError: inline error row for the panel
 *  *   MetricsEmpty: placeholder shown before first payload
 *  *   clusterSizeBucket(): buckets duplicate clusters by size
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
    return (
      <div className="metrics-panel metrics-error">metrics unavailable</div>
    );
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
        <li key={cluster.folded}>{cluster.variants.join(" / ")}</li>
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

export const METRICS_REFRESH_MS = 30_000;

/**
 * Renders a button triggering an immediate metrics reload.
 *
 * @param props.onRefresh - Called when the button is pressed.
 * @param props.busy - Whether a refresh is already in flight.
 * @returns element - Refresh button with busy state.
 */
export function RefreshButton({ onRefresh, busy }) {
  return (
    <button
      type="button"
      className="metrics-refresh-button"
      onClick={onRefresh}
      disabled={busy}
    >
      {busy ? "refreshing…" : "refresh"}
    </button>
  );
}

/**
 * Polls the metrics endpoint on the shared refresh cadence.
 *
 * @param onPayload - Called with every successful metrics payload.
 * @returns state - { busy, refresh } refresh state and manual trigger.
 */
export function useMetricsRefresh(onPayload) {
  const [busy, setBusy] = useState(false);
  const refresh = () => {
    setBusy(true);
    fetchDedupMetrics()
      .then(onPayload)
      .finally(() => setBusy(false));
  };
  useEffect(() => {
    const handle = setInterval(refresh, METRICS_REFRESH_MS);
    return () => clearInterval(handle);
  }, []);
  return { busy, refresh };
}

/**
 * Renders an inline error row when metrics fail to load.
 *
 * @param props.message - Error detail to display.
 * @returns element - Inline error row.
 */
export function MetricsError({ message }) {
  return (
    <p className="metrics-error">
      metrics unavailable{message ? `: ${message}` : ""}
    </p>
  );
}

/**
 * Renders the placeholder shown before the first metrics payload arrives.
 *
 * @returns element - Empty-state panel body.
 */
export function MetricsEmpty() {
  return <p className="metrics-note">gathering graph metrics…</p>;
}

/**
 * Buckets duplicate clusters by variant count for the summary line.
 *
 * @param clusters - Duplicate cluster list from the metrics payload.
 * @returns buckets - { small, medium, large } cluster counts.
 */
export function clusterSizeBucket(clusters) {
  const buckets = { small: 0, medium: 0, large: 0 };
  for (const cluster of clusters) {
    const size = cluster.variants.length;
    if (size <= 2) {
      buckets.small += 1;
    } else if (size <= 4) {
      buckets.medium += 1;
    } else {
      buckets.large += 1;
    }
  }
  return buckets;
}
