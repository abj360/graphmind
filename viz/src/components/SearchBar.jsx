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
 *  *   ClearButton: resets the current query
 *  *   compileSafeRegex(): parses a regex query, tolerating bad input
 *  *   matchesRegex(): checks a node against a compiled pattern
 *  *   RegexToggle: switches between substring and regex modes
 *  *   SearchHelp: hint text for the active search mode
 *  *   isQueryEmpty(): shared empty-query check
 *  *   highlightMatch(): wraps matched text in a marker class
 *  *   recentSearches(): tiny in-memory recent-query list
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
    node.label.toLowerCase().includes(query) ||
    node.type.toLowerCase().includes(query)
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
      <input
        type="checkbox"
        checked={checked}
        onChange={() => onToggle(!checked)}
      />
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

/**
 * Renders a button clearing the current query.
 *
 * @param props.visible - Whether the button renders at all.
 * @param props.onClear - Called when the button is pressed.
 * @returns element - Clear button, or null when hidden.
 */
export function ClearButton({ visible, onClear }) {
  if (!visible) {
    return null;
  }
  return (
    <button
      type="button"
      className="search-clear"
      onClick={onClear}
      aria-label="clear filter"
    >
      ×
    </button>
  );
}

/**
 * Parses a query as a regular expression, tolerating invalid patterns.
 *
 * @param query - Raw pattern text from the search input.
 * @returns regex - Compiled RegExp, or null when the pattern is invalid.
 */
export function compileSafeRegex(query) {
  if (!query) {
    return null;
  }
  try {
    return new RegExp(query, "i");
  } catch {
    return null;
  }
}

/**
 * Checks whether a node matches a compiled regular expression.
 *
 * @param node - View-graph node with label and type.
 * @param regex - Compiled pattern from compileSafeRegex().
 * @returns matches - True when the label or type matches the pattern.
 */
export function matchesRegex(node, regex) {
  if (!regex) {
    return true;
  }
  return regex.test(node.label) || regex.test(node.type);
}

/**
 * Renders the substring/regex mode toggle next to the search input.
 *
 * @param props.enabled - Whether regex mode is active.
 * @param props.onToggle - Called with the new mode state.
 * @returns element - Mode toggle button.
 */
export function RegexToggle({ enabled, onToggle }) {
  return (
    <button
      type="button"
      className={enabled ? "regex-toggle regex-toggle-on" : "regex-toggle"}
      onClick={() => onToggle(!enabled)}
      title="toggle regex matching"
      aria-pressed={enabled}
    >
      .*
    </button>
  );
}

/**
 * Renders a short hint describing the active search mode.
 *
 * @param props.regexMode - Whether regex mode is active.
 * @returns element - Hint line under the search input.
 */
export function SearchHelp({ regexMode }) {
  return (
    <p className="search-help">
      {regexMode
        ? "regex mode: patterns like ^acme|corp$ work"
        : "substring mode: plain text filter"}
    </p>
  );
}

/**
 * Checks whether a search query is effectively empty.
 *
 * @param query - Raw query text.
 * @returns empty - True when the trimmed query has no characters.
 */
export function isQueryEmpty(query) {
  return query.trim().length === 0;
}

/**
 * Wraps the matched portion of a label in a highlight marker.
 *
 * @param label - Full node label.
 * @param query - Active raw query text.
 * @returns parts - { before, match, after } segments for rendering.
 */
export function highlightMatch(label, query) {
  const index = label.toLowerCase().indexOf(query.trim().toLowerCase());
  if (!query.trim() || index < 0) {
    return { before: label, match: "", after: "" };
  }
  return {
    before: label.slice(0, index),
    match: label.slice(index, index + query.trim().length),
    after: label.slice(index + query.trim().length),
  };
}

const RECENT_LIMIT = 5;

/**
 * Maintains a tiny in-memory list of recently used queries.
 *
 * @returns api - { list, push } recent-search state helpers.
 */
export function recentSearches() {
  const items = [];
  return {
    list: () => [...items],
    push: (query) => {
      const normalized = query.trim();
      if (!normalized || items[0] === normalized) {
        return;
      }
      items.unshift(normalized);
      if (items.length > RECENT_LIMIT) {
        items.pop();
      }
    },
  };
}
