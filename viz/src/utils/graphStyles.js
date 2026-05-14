#!/usr/bin/env node
/**
 * graphStyles.js --- cytoscape style builders and layout constants for the viewer
 *  *
 *  * Contains:
 *  *   GRAPH_LAYOUT: default force-directed layout options
 *  *   TYPE_COLORS: entity type to color mapping
 *  *   colorForType(): resolves a type to its palette color
 *  *   buildNodeStyle(): cytoscape node style block
 *  *   buildTypeSelectors(): per-type color override selectors
 *  *   buildEdgeStyle(): cytoscape edge style block
 *  *   buildInferredEdgeStyle(): dashed style for inferred edges
 *  *   buildSelfLoopStyle(): curved style for self-loop edges
 *  *   buildParallelEdgeStyles(): fanned curves for parallel edges
 *  *   buildFullStylesheet(): composes every style block
 *  *   buildSelectedNodeStyle(): highlight for the selected node
 *  *   buildDimmedStyle(): fades non-matching elements
 *  *   buildEdgeLabelStyle(): edge label styling rules
 *  *   buildHoverStyle(): subtle highlight on hover
 *  *   fontFamilyFor(): consistent font stack token
 *  *   buildCompoundNodeSizing(): degree-scaled node diameters
 *  *   buildEdgeConfidenceColor(): confidence-to-color mapping
 */

export const GRAPH_LAYOUT = {
  name: "cose",
  animate: false,
  nodeRepulsion: 8000,
  idealEdgeLength: 120,
  padding: 40,
};

export const TYPE_COLORS = {
  PERSON: "#f4a261",
  ORG: "#2a9d8f",
  GPE: "#e9c46a",
  SOFTWARE: "#457b9d",
  CONCEPT: "#8d99ae",
  GENE: "#9b5de5",
  DISEASE: "#ef476f",
  DRUG: "#06d6a0",
  PATHWAY: "#118ab2",
};

/**
 * Resolves an entity type to its palette color.
 *
 * @param type - Entity type label such as PERSON or ORG.
 * @returns color - Hex color from TYPE_COLORS, grey for unknown types.
 */
export function colorForType(type) {
  return TYPE_COLORS[type] ?? "#6c757d";
}

/**
 * Builds the Cytoscape node style block using the type palette.
 *
 * @returns style - Cytoscape style definition for nodes.
 */
export function buildNodeStyle() {
  return {
    selector: "node",
    style: {
      label: "data(label)",
      "font-size": 10,
      "text-wrap": "wrap",
      "text-max-width": 90,
      "text-valign": "bottom",
      "text-margin-y": 6,
      width: 22,
      height: 22,
      "border-width": 1,
      "border-color": "#1d3557",
    },
  };
}

/**
 * Builds per-type color override selectors for the palette.
 *
 * @returns selectors - Cytoscape style list, one entry per known type.
 */
export function buildTypeSelectors() {
  return Object.entries(TYPE_COLORS).map(([type, color]) => ({
    selector: `node[type = "${type}"]`,
    style: { "background-color": color },
  }));
}

/**
 * Builds the Cytoscape edge style block with arrows and curves.
 *
 * @returns style - Cytoscape style definition for edges.
 */
export function buildEdgeStyle() {
  return {
    selector: "edge",
    style: {
      "curve-style": "bezier",
      "target-arrow-shape": "triangle",
      "arrow-scale": 0.8,
      "line-color": "#adb5bd",
      "target-arrow-color": "#adb5bd",
      width: 2,
      opacity: 0.85,
    },
  };
}

/**
 * Builds the dashed style override for inferred edges.
 *
 * @returns style - Cytoscape style definition for inferred edges.
 */
export function buildInferredEdgeStyle() {
  return {
    selector: "edge[inferred]",
    style: {
      "line-style": "dashed",
      "line-color": "#dee2e6",
      "target-arrow-color": "#dee2e6",
    },
  };
}

/**
 * Builds the loop curve style override for self-loop edges.
 *
 * @returns style - Cytoscape style definition for self-loops.
 */
export function buildSelfLoopStyle() {
  return {
    selector: "edge:loop",
    style: {
      "curve-style": "bezier",
      "loop-direction": "0deg",
      "loop-sweep": "45deg",
    },
  };
}

/**
 * Builds fanned curve overrides for parallel edge groups.
 *
 * @param maxParallel - Largest parallel group size to cover.
 * @returns styles - One style entry per parallel index.
 */
export function buildParallelEdgeStyles(maxParallel = 4) {
  const styles = [];
  for (let index = 1; index <= maxParallel; index += 1) {
    styles.push({
      selector: `edge[parallelIndex = ${index}]`,
      style: {
        "curve-style": "bezier",
        "control-point-step-size": 24 * index,
      },
    });
  }
  return styles;
}

/**
 * Composes the full Cytoscape stylesheet from every style block.
 *
 * @returns stylesheet - Complete style list for the viewer.
 */
export function buildFullStylesheet() {
  return [
    buildNodeStyle(),
    ...buildTypeSelectors(),
    buildEdgeStyle(),
    buildInferredEdgeStyle(),
    buildSelfLoopStyle(),
    ...buildParallelEdgeStyles(),
  ];
}

/**
 * Builds the highlight style for the currently selected node.
 *
 * @returns style - Cytoscape style definition for the selected node.
 */
export function buildSelectedNodeStyle() {
  return {
    selector: "node:selected",
    style: {
      "border-width": 3,
      "border-color": "#e9c46a",
    },
  };
}

/**
 * Builds the dimmed style applied to filtered-out elements.
 *
 * @returns style - Cytoscape style definition for dimmed elements.
 */
export function buildDimmedStyle() {
  return {
    selector: ".dimmed",
    style: {
      opacity: 0.15,
      "text-opacity": 0.2,
    },
  };
}

/**
 * Builds the edge label styling rules for readable density.
 *
 * @returns style - Cytoscape style definition for edge labels.
 */
export function buildEdgeLabelStyle() {
  return {
    selector: "edge[label]",
    style: {
      label: "data(label)",
      "font-size": 8,
      "text-rotation": "autorotate",
      "text-margin-y": -6,
      color: "#9fb0c7",
    },
  };
}

/**
 * Builds the subtle highlight style applied on element hover.
 *
 * @returns style - Cytoscape style definition for hovered elements.
 */
export function buildHoverStyle() {
  return {
    selector: "node:active",
    style: {
      "overlay-color": "#e9c46a",
      "overlay-opacity": 0.15,
    },
  };
}

export const GRAPH_FONT_FAMILY = "Inter, Segoe UI, system-ui, sans-serif";

/**
 * Builds degree-scaled node sizing overrides for hub visibility.
 *
 * @returns style - Cytoscape style definition scaling nodes by degree.
 */
export function buildCompoundNodeSizing() {
  return {
    selector: "node",
    style: {
      width: "mapData(degree, 0, 20, 18, 42)",
      height: "mapData(degree, 0, 20, 18, 42)",
    },
  };
}

/**
 * Builds the confidence-to-color mapping for edge lines.
 *
 * @returns style - Cytoscape style definition coloring edges by confidence.
 */
export function buildEdgeConfidenceColor() {
  return {
    selector: "edge[confidence]",
    style: {
      "line-color": "mapData(confidence, 0, 1, #495057, #06d6a0)",
      "target-arrow-color": "mapData(confidence, 0, 1, #495057, #06d6a0)",
    },
  };
}
