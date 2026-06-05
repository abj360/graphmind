#!/usr/bin/env node
/**
 * GraphLegend.jsx --- legend mapping entity types to their palette colors
 *  *
 *  * Contains:
 *  *   GraphLegend: type-to-color legend overlay
 */

import { colorForType } from "../utils/graphStyles.js";

/**
 * Renders the legend mapping entity types to palette colors.
 *
 * @param props.nodes - Visible nodes used to list present types.
 * @returns element - Legend overlay listing present types.
 */
export default function GraphLegend({ nodes }) {
  const types = [...new Set(nodes.map((node) => node.type))].sort();
  if (types.length === 0) {
    return null;
  }
  return (
    <ul className="graph-legend">
      {types.map((type) => (
        <li key={type}>
          <span className="legend-swatch" style={{ backgroundColor: colorForType(type) }} />
          {type}
        </li>
      ))}
    </ul>
  );
}
