/**
 * graphMotion.js --- the slow drift and firing pulse applied to a laid-out graph
 *
 * Contains:
 *   DRIFT: amplitude, period, and firing cadence of the motion
 *   prefersReducedMotion(): whether the viewer asked for stillness
 *   seedPhase(): a stable per-node phase from its id
 *   driftOffset(): where one node sits at a given moment
 *   startMotion(): runs the drift and pulse until the returned stop() is called
 *
 * A node the viewer is dragging is left alone, and where they drop it becomes
 * its new anchor, so the drift never fights the pointer.
 */

export const DRIFT = {
  amplitudeX: 9,
  amplitudeY: 7,
  periodMs: 11000,
  firingIntervalMs: 420,
  firingHoldMs: 1100,
  firingFraction: 0.06,
};

export function prefersReducedMotion() {
  /**
   * Reports whether the viewer has asked for reduced motion.
   *
   * @returns reduced - True when the environment asks for stillness.
   */
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

export function seedPhase(id) {
  /**
   * Derives a stable phase offset from a node id.
   *
   * Nodes have to drift out of step with each other or the whole graph slides
   * as one block, and the offset has to survive a re-render, so it comes from
   * the id rather than a random draw.
   *
   * @param id - Node identifier.
   * @returns phase - Phase offset in radians.
   */
  let hash = 0;
  for (let index = 0; index < id.length; index += 1) {
    hash = (hash * 31 + id.charCodeAt(index)) % 100000;
  }
  return (hash / 100000) * Math.PI * 2;
}

export function driftOffset(phase, elapsedMs, drift = DRIFT) {
  /**
   * Computes one node's displacement from its laid-out position.
   *
   * The two axes use different multiples of the period so a node traces a slow
   * loop rather than sliding along a diagonal.
   *
   * @param phase - The node's phase offset in radians.
   * @param elapsedMs - Milliseconds since the motion started.
   * @param drift - Amplitude and period settings.
   * @returns offset - { x, y } displacement in graph units.
   */
  const turn = (elapsedMs / drift.periodMs) * Math.PI * 2;
  return {
    x: Math.sin(turn + phase) * drift.amplitudeX,
    y: Math.cos(turn * 0.73 + phase) * drift.amplitudeY,
  };
}

export function startMotion(cy, drift = DRIFT) {
  /**
   * Drifts the laid-out graph and pulses nodes until stopped.
   *
   * Positions are held relative to the layout result rather than accumulated,
   * so the graph breathes around its layout instead of wandering away from it.
   *
   * @param cy - Cytoscape instance whose layout has settled.
   * @param drift - Amplitude, period, and firing cadence.
   * @returns stop - Function that halts the motion and restores positions.
   */
  if (prefersReducedMotion()) {
    return () => {};
  }

  const anchors = new Map();
  cy.nodes().forEach((node) => {
    const position = node.position();
    anchors.set(node.id(), {
      x: position.x,
      y: position.y,
      phase: seedPhase(node.id()),
    });
  });

  const started = performance.now();
  let frame = 0;

  const step = (now) => {
    const elapsed = now - started;
    cy.batch(() => {
      cy.nodes().forEach((node) => {
        const anchor = anchors.get(node.id());
        if (anchor === undefined || node.grabbed()) {
          return;
        }
        const offset = driftOffset(anchor.phase, elapsed, drift);
        node.position({ x: anchor.x + offset.x, y: anchor.y + offset.y });
      });
    });
    frame = requestAnimationFrame(step);
  };
  frame = requestAnimationFrame(step);

  const pulse = setInterval(() => {
    const nodes = cy.nodes();
    if (nodes.length === 0) {
      return;
    }
    const count = Math.max(1, Math.round(nodes.length * drift.firingFraction));
    for (let index = 0; index < count; index += 1) {
      const node = nodes[Math.floor(Math.random() * nodes.length)];
      node.addClass("firing");
      setTimeout(() => node.removeClass("firing"), drift.firingHoldMs);
    }
  }, drift.firingIntervalMs);

  const reanchor = (event) => {
    const node = event.target;
    const anchor = anchors.get(node.id());
    if (anchor === undefined) {
      return;
    }
    const offset = driftOffset(
      anchor.phase,
      performance.now() - started,
      drift,
    );
    const dropped = node.position();
    anchors.set(node.id(), {
      x: dropped.x - offset.x,
      y: dropped.y - offset.y,
      phase: anchor.phase,
    });
  };
  cy.on("dragfree", "node", reanchor);

  return () => {
    cancelAnimationFrame(frame);
    clearInterval(pulse);
    cy.removeListener("dragfree", "node", reanchor);
    cy.batch(() => {
      cy.nodes().forEach((node) => {
        const anchor = anchors.get(node.id());
        if (anchor !== undefined) {
          node.position({ x: anchor.x, y: anchor.y });
        }
      });
    });
    cy.nodes().removeClass("firing");
  };
}
