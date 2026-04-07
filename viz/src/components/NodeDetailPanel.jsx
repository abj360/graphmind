#!/usr/bin/env node
/**
 * NodeDetailPanel.jsx --- side panel showing details of the selected node
 *  *
 *  * Contains:
 *  *   NodeDetailPanel: selected-node detail view
 *  *   IncidentEdge: one relationship row in the panel
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
