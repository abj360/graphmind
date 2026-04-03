#!/usr/bin/env node
/**
 * SearchBar.jsx --- search and filter controls for the graph viewer
 *  *
 *  * Contains:
 *  *   SearchBar: query input with result count
 *  *   normalizeQuery(): trims and case-folds filter text
 *  *   matchesQuery(): checks a node against the filter
 *  *   FilterToggle: checkbox row for optional filters
 *  *   typeAheadCandidates(): label suggestions for the query
 */

/**
 * Renders the search input filtering the visible graph.
 *
 * @param props.query - Current filter text.
 * @param props.onChange - Called with the new filter text on every edit.
 * @param props.resultCount - Optional count of visible nodes to display.
 * @returns element - Search control row.
 */
export default function SearchBar({ query, onChange, resultCount }) {
  return (
    <div className="search-bar">
      <input
        type="search"
        className="search-input"
        placeholder="filter entities…"
        value={query}
        onChange={(event) => onChange(event.target.value)}
        aria-label="filter entities"
      />
      {typeof resultCount === "number" && (
        <span className="search-count">{resultCount} shown</span>
      )}
    </div>
  );
}

/**
 * Trims and case-folds raw filter text.
 *
 * @param query - Raw filter text from the input.
 * @returns normalized - Trimmed, lowercased query.
 */
export function normalizeQuery(query) {
  return query.trim().toLowerCase();
}

/**
 * Checks whether a node matches the current filter text.
 *
 * @param node - View-graph node with label and type.
 * @param query - Normalized filter text.
 * @returns matches - True when the label or type contains the query.
 */
export function matchesQuery(node, query) {
  if (!query) {
    return true;
  }
  return (
    node.label.toLowerCase().includes(query) || node.type.toLowerCase().includes(query)
  );
}

/**
 * Renders a labeled checkbox row for an optional filter.
 *
 * @param props.label - Human-readable filter label.
 * @param props.checked - Current toggle state.
 * @param props.onToggle - Called with the new state.
 * @returns element - Labeled checkbox row.
 */
export function FilterToggle({ label, checked, onToggle }) {
  return (
    <label className="filter-toggle">
      <input type="checkbox" checked={checked} onChange={() => onToggle(!checked)} />
      {label}
    </label>
  );
}

/**
 * Computes type-ahead label suggestions for the current query.
 *
 * @param nodes - Visible node list to suggest from.
 * @param query - Raw query text.
 * @param limit - Maximum suggestions returned.
 * @returns suggestions - Matching labels, alphabetically sorted.
 */
export function typeAheadCandidates(nodes, query, limit = 6) {
  const normalized = normalizeQuery(query);
  if (!normalized) {
    return [];
  }
  return nodes
    .filter((node) => matchesQuery(node, normalized))
    .map((node) => node.label)
    .sort()
    .slice(0, limit);
}
