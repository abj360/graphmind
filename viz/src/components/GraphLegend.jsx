/**
 * GraphLegend.jsx --- legend mapping entity types to their palette colors
 *  *
 *  * Contains:
 *  *   GraphLegend: type-to-color legend overlay
 *  *   countByType(): tallies visible nodes per type
 *  *   legendItemId(): stable key for legend entries
 */

import { colorForType } from "../utils/graphStyles.js";

/**
 * Renders the legend mapping entity types to palette colors.
 *
 * @param props.nodes - Visible nodes used to list present types.
 * @returns element - Legend overlay listing present types.
 */
export default function GraphLegend({ nodes }) {
  const counts = countByType(nodes);
  if (counts.length === 0) {
    return null;
  }
  return (
    <ul className="graph-legend">
      {counts.map(([type, count]) => (
        <li key={legendItemId(type)}>
          <span
            className="legend-swatch"
            style={{ backgroundColor: colorForType(type) }}
          />
          {type}
          <span className="legend-count">{count}</span>
        </li>
      ))}
    </ul>
  );
}

/**
 * Tallies visible nodes per entity type for the legend.
 *
 * @param nodes - Visible node list.
 * @returns counts - Sorted [type, count] entries, most common first.
 */
export function countByType(nodes) {
  const counts = new Map();
  for (const node of nodes) {
    counts.set(node.type, (counts.get(node.type) ?? 0) + 1);
  }
  return [...counts.entries()].sort((left, right) => right[1] - left[1]);
}

/**
 * Builds a stable React key for one legend entry.
 *
 * @param type - Entity type the entry represents.
 * @returns key - Stable, human-readable key string.
 */
export function legendItemId(type) {
  return `legend-${type.toLowerCase()}`;
}
