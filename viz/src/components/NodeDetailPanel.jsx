#!/usr/bin/env node
/**
 * NodeDetailPanel.jsx --- side panel showing details of the selected node
 *  *
 *  * Contains:
 *  *   NodeDetailPanel: selected-node detail view
 *  *   IncidentEdge: one relationship row in the panel
 *  *   confidenceBadge(): color hint for a confidence score
 *  *   groupByDirection(): splits incident edges by direction
 *  *   sortByConfidence(): orders edges strongest first
 *  *   truncateLabel(): caps long labels with an ellipsis
 *  *   relatedTypes(): entity types neighboring the selection
 */

/**
 * Renders details and incident edges of the currently selected node.
 *
 * @param props.node - Selected node data, or null for an empty panel.
 * @param props.edges - Full edge list used to find incident edges.
 * @param props.onClose - Called when the panel is dismissed.
 * @returns element - Detail panel, or a placeholder when nothing is selected.
 */
export default function NodeDetailPanel({ node, edges, onClose }) {
  if (!node) {
    return <div className="detail-panel detail-empty">select a node to inspect it</div>;
  }
  const incident = edges.filter((edge) => edge.source === node.id || edge.target === node.id);
  return (
    <div className="detail-panel">
      <header className="detail-header">
        <h2>{node.label}</h2>
        <button type="button" className="detail-close" onClick={onClose} aria-label="close">
          ×
        </button>
      </header>
      <p className="detail-type">{node.type}</p>
      <h3>relationships ({incident.length})</h3>
      <ul className="detail-edges">
        {incident.map((edge) => (
          <IncidentEdge key={edge.id} edge={edge} focus={node.id} />
        ))}
      </ul>
    </div>
  );
}

/**
 * Renders one incident relationship row relative to the focused node.
 *
 * @param props.edge - Edge incident to the focused node.
 * @param props.focus - Id of the focused node, orienting the row.
 * @returns element - Relationship list item.
 */
function IncidentEdge({ edge, focus }) {
  const outgoing = edge.source === focus;
  const other = outgoing ? edge.target : edge.source;
  return (
    <li className="detail-edge">
      <span className="detail-direction">{outgoing ? "→" : "←"}</span>
      <span className="detail-predicate">{edge.predicate}</span>
      <span className="detail-other">{other}</span>
      {typeof edge.confidence === "number" && (
        <span className="detail-confidence">{edge.confidence.toFixed(2)}</span>
      )}
    </li>
  );
}

/**
 * Picks a CSS class hinting at a confidence score's strength.
 *
 * @param confidence - Score between 0 and 1.
 * @returns className - Badge class name for the score bucket.
 */
export function confidenceBadge(confidence) {
  if (confidence >= 0.8) {
    return "badge-high";
  }
  if (confidence >= 0.5) {
    return "badge-mid";
  }
  return "badge-low";
}

/**
 * Splits incident edges into outgoing and incoming groups.
 *
 * @param edges - Edges incident to the focused node.
 * @param focus - Id of the focused node.
 * @returns groups - { outgoing, incoming } edge lists.
 */
export function groupByDirection(edges, focus) {
  const outgoing = [];
  const incoming = [];
  for (const edge of edges) {
    if (edge.source === focus) {
      outgoing.push(edge);
    } else {
      incoming.push(edge);
    }
  }
  return { outgoing, incoming };
}

/**
 * Orders edges by confidence, strongest first, nulls last.
 *
 * @param edges - Edge list to sort.
 * @returns edges - Sorted copy of the input list.
 */
export function sortByConfidence(edges) {
  return [...edges].sort((left, right) => (right.confidence ?? -1) - (left.confidence ?? -1));
}

/**
 * Caps long labels with an ellipsis for narrow panels.
 *
 * @param label - Full label text.
 * @param maxLength - Maximum characters before truncation.
 * @returns label - Original or truncated label.
 */
export function truncateLabel(label, maxLength = 28) {
  if (label.length <= maxLength) {
    return label;
  }
  return `${label.slice(0, maxLength - 1)}…`;
}

/**
 * Lists entity types neighboring the selected node, most frequent first.
 *
 * @param node - Selected node data.
 * @param edges - Full edge list.
 * @param nodes - Full node list for type lookup.
 * @returns types - Neighboring entity types, deduplicated and sorted by count.
 */
export function relatedTypes(node, edges, nodes) {
  if (!node) {
    return [];
  }
  const typeOf = new Map(nodes.map((entry) => [entry.id, entry.type]));
  const counts = new Map();
  for (const edge of edges) {
    const other = edge.source === node.id ? edge.target : edge.target === node.id ? edge.source : null;
    if (other) {
      const type = typeOf.get(other) ?? "CONCEPT";
      counts.set(type, (counts.get(type) ?? 0) + 1);
    }
  }
  return [...counts.entries()].sort((left, right) => right[1] - left[1]).map(([type]) => type);
}
