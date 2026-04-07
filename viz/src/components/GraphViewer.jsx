#!/usr/bin/env node
/**
 * GraphViewer.jsx --- Cytoscape.js canvas rendering the knowledge graph
 *  *
 *  * Contains:
 *  *   toElements(): maps view graph to cytoscape elements
 *  *   GraphViewer: cytoscape canvas component
 */

import cytoscape from "cytoscape";
import { useEffect, useRef } from "react";

/**
 * Maps a view graph into Cytoscape element definitions.
 *
 * @param graph - { nodes, edges } payload from the BFF.
 * @returns elements - Cytoscape element list.
 */
export function toElements(graph) {
  const nodes = graph.nodes.map((node) => ({
    data: { id: node.id, label: node.label, type: node.type },
  }));
  const edges = graph.edges.map((edge) => ({
    data: {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      predicate: edge.predicate,
      confidence: edge.confidence,
      inferred: edge.inferred,
    },
  }));
  return [...nodes, ...edges];
}

/**
 * Renders the knowledge graph on a Cytoscape canvas.
 *
 * @param props.graph - { nodes, edges } payload to render.
 * @param props.onSelectNode - Callback fired with the tapped node's data.
 * @returns element - Canvas container element.
 */
export default function GraphViewer({ graph, onSelectNode }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);

  useEffect(() => {
    const cy = cytoscape({
      container: containerRef.current,
      elements: toElements(graph),
      layout: { name: "cose", animate: false },
      style: [
        {
          selector: "node",
          style: { label: "data(label)", "font-size": 10 },
        },
        {
          selector: "edge",
          style: { "curve-style": "haystack", width: 2 },
        },
      ],
    });
    if (onSelectNode) {
      cy.on("tap", "node", (event) => onSelectNode(event.target.data()));
      cy.on("tap", (event) => {
        if (event.target === cy) {
          onSelectNode(null);
        }
      });
    }
    cyRef.current = cy;
    return () => cy.destroy();
  }, [graph, onSelectNode]);

  return <div ref={containerRef} className="graph-canvas" />;
}
