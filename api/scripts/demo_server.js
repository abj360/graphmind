#!/usr/bin/env node
/**
 * demo_server.js --- serves the BFF from a seeded in-memory graph
 *  *
 *  * Lets the API and viewer be driven without a Neo4j instance. Nothing here
 *  * reaches a database and it is not a production path.
 *  *
 *  * Contains:
 *  *   TRIPLES: the seeded corpus
 *  *   memoryDriver(): driver double answering the routes' queries
 *  *   main(): serves the demo API
 */

import { createApp } from "../src/app.js";
import { loadConfig } from "../src/config.js";

const TRIPLES = [
  ["Ada Lovelace", "PERSON", "collaborated with", "Charles Babbage", "PERSON", 0.96],
  ["Ada Lovelace", "PERSON", "wrote notes on", "Analytical Engine", "ARTIFACT", 0.94],
  ["Charles Babbage", "PERSON", "designed", "Analytical Engine", "ARTIFACT", 0.98],
  ["Charles Babbage", "PERSON", "designed", "Difference Engine", "ARTIFACT", 0.97],
  ["Analytical Engine", "ARTIFACT", "influenced", "Stored Program Computer", "CONCEPT", 0.81],
  ["Alan Turing", "PERSON", "formalised", "Stored Program Computer", "CONCEPT", 0.89],
  ["Alan Turing", "PERSON", "worked at", "Bletchley Park", "ORG", 0.93],
  ["Alan Turing", "PERSON", "published", "On Computable Numbers", "ARTIFACT", 0.99],
  ["On Computable Numbers", "ARTIFACT", "introduced", "Turing Machine", "CONCEPT", 0.99],
  ["Turing Machine", "CONCEPT", "underpins", "Computability Theory", "CONCEPT", 0.9],
  ["Bletchley Park", "ORG", "employed", "Joan Clarke", "PERSON", 0.92],
  ["Joan Clarke", "PERSON", "worked on", "Enigma", "ARTIFACT", 0.88],
  ["Enigma", "ARTIFACT", "encrypted", "Naval Signals", "CONCEPT", 0.84],
  ["Grace Hopper", "PERSON", "developed", "COBOL", "ARTIFACT", 0.95],
  ["Grace Hopper", "PERSON", "served in", "US Navy", "ORG", 0.91],
  ["COBOL", "ARTIFACT", "influenced", "Business Computing", "CONCEPT", 0.8],
  ["Claude Shannon", "PERSON", "founded", "Information Theory", "CONCEPT", 0.97],
  ["Information Theory", "CONCEPT", "underpins", "Computability Theory", "CONCEPT", 0.76],
  ["Claude Shannon", "PERSON", "worked at", "Bell Labs", "ORG", 0.94],
  ["Bell Labs", "ORG", "produced", "Transistor", "ARTIFACT", 0.96],
  ["Transistor", "ARTIFACT", "enabled", "Stored Program Computer", "CONCEPT", 0.87],
  ["Barbara Liskov", "PERSON", "formalised", "Substitution Principle", "CONCEPT", 0.95],
  ["Barbara Liskov", "PERSON", "worked at", "MIT", "ORG", 0.93],
  ["MIT", "ORG", "produced", "CLU", "ARTIFACT", 0.85],
  ["CLU", "ARTIFACT", "influenced", "Abstract Data Types", "CONCEPT", 0.88],
  ["Substitution Principle", "CONCEPT", "underpins", "Abstract Data Types", "CONCEPT", 0.79],
];

const TYPES = new Map(
  TRIPLES.flatMap(([s, st, , o, ot]) => [
    [s, st],
    [o, ot],
  ]),
);

const node = (name) => ({ properties: { name, entity_type: TYPES.get(name) ?? "CONCEPT" } });
const rel = (predicate, confidence, inferred) => ({
  properties: { predicate, confidence, inferred },
});
const record = (values) => ({ get: (key) => (key in values ? values[key] : null) });
const integer = (value) => ({ toNumber: () => value });

/**
 * Builds a driver double that answers each route query from TRIPLES.
 *
 * @returns driver - Object exposing the session()/close() surface routes use.
 */
function memoryDriver() {
  const rows = TRIPLES.map(([s, , predicate, o, , confidence], index) =>
    record({ n: node(s), r: rel(predicate, confidence, index % 9 === 8), m: node(o) }),
  );

  const answer = (query, params) => {
    if (query.includes("count(n) AS total")) {
      return [record({ total: integer(TYPES.size), types: [...new Set(TYPES.values())] })];
    }
    if (query.includes("count(r) AS total")) {
      const mean = TRIPLES.reduce((sum, t) => sum + t[5], 0) / TRIPLES.length;
      return [
        record({
          total: integer(TRIPLES.length),
          predicates: integer(new Set(TRIPLES.map((t) => t[2])).size),
          meanConfidence: Number(mean.toFixed(3)),
        }),
      ];
    }
    if (query.includes("toLower(n.name) AS folded")) {
      return [];
    }
    if (query.includes("count(r) AS degree")) {
      const degrees = new Map();
      for (const [s, , , o] of TRIPLES) {
        degrees.set(s, (degrees.get(s) ?? 0) + 1);
        degrees.set(o, (degrees.get(o) ?? 0) + 1);
      }
      return [...degrees.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([name, degree]) => record({ name, degree: integer(degree) }));
    }
    if (query.includes("RETURN DISTINCT n.entity_type")) {
      const counts = new Map();
      for (const type of TYPES.values()) {
        counts.set(type, (counts.get(type) ?? 0) + 1);
      }
      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => record({ type, count: integer(count) }));
    }
    if (query.includes("{name: $name}")) {
      const name = params.name;
      if (!TYPES.has(name)) {
        return [];
      }
      const touching = rows.filter(
        (row) => row.get("n").properties.name === name || row.get("m").properties.name === name,
      );
      return touching.length > 0 ? touching : [record({ n: node(name) })];
    }
    return rows.slice(0, params.limit ?? rows.length);
  };

  return {
    session: () => ({
      run: async (query, params = {}) => ({ records: answer(query, params) }),
      close: async () => {},
    }),
    close: async () => {},
  };
}

/**
 * Serves the demo API until interrupted.
 */
function main() {
  const config = loadConfig();
  createApp(memoryDriver(), config).listen(config.port, () => {
    console.log(`graphmind-api (demo data) listening on :${config.port}`);
  });
}

main();
