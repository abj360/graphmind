#!/usr/bin/env node
/**
 * SearchBar.jsx --- search and filter controls for the graph viewer
 *  *
 *  * Contains:
 *  *   SearchBar: query input with result count
 *  *   normalizeQuery(): trims and case-folds filter text
 *  *   matchesQuery(): checks a node against the filter
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
