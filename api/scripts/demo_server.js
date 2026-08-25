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
  ["Guido van Rossum", "PERSON", "created", "Python", "SOFTWARE", 0.98],
  ["Guido van Rossum", "PERSON", "worked at", "Dropbox", "ORG", 0.91],
  ["Python", "SOFTWARE", "implements", "Duck Typing", "CONCEPT", 0.88],
  ["Python", "SOFTWARE", "influenced", "TypeScript", "SOFTWARE", 0.72],
  ["Anders Hejlsberg", "PERSON", "created", "TypeScript", "SOFTWARE", 0.97],
  ["Anders Hejlsberg", "PERSON", "works at", "Microsoft", "ORG", 0.95],
  ["Microsoft", "ORG", "maintains", "TypeScript", "SOFTWARE", 0.96],
  ["Microsoft", "ORG", "headquartered in", "Redmond", "GPE", 0.93],
  ["TypeScript", "SOFTWARE", "compiles to", "JavaScript", "SOFTWARE", 0.99],
  ["TypeScript", "SOFTWARE", "implements", "Structural Typing", "CONCEPT", 0.9],
  ["Brendan Eich", "PERSON", "created", "JavaScript", "SOFTWARE", 0.98],
  ["Brendan Eich", "PERSON", "co-founded", "Mozilla", "ORG", 0.94],
  ["Mozilla", "ORG", "maintains", "Rust", "SOFTWARE", 0.86],
  ["Graydon Hoare", "PERSON", "created", "Rust", "SOFTWARE", 0.97],
  ["Rust", "SOFTWARE", "implements", "Ownership", "CONCEPT", 0.95],
  ["Ownership", "CONCEPT", "generalises", "Memory Safety", "CONCEPT", 0.84],
  ["Rust", "SOFTWARE", "influenced", "Swift", "SOFTWARE", 0.68],
  ["Chris Lattner", "PERSON", "created", "Swift", "SOFTWARE", 0.96],
  ["Chris Lattner", "PERSON", "created", "LLVM", "SOFTWARE", 0.98],
  ["Swift", "SOFTWARE", "compiles with", "LLVM", "SOFTWARE", 0.93],
  ["Apple", "ORG", "maintains", "Swift", "SOFTWARE", 0.95],
  ["Apple", "ORG", "headquartered in", "Cupertino", "GPE", 0.94],
  ["Barbara Liskov", "PERSON", "formalised", "Substitution Principle", "CONCEPT", 0.95],
  ["Barbara Liskov", "PERSON", "worked at", "MIT", "ORG", 0.93],
  ["MIT", "ORG", "headquartered in", "Cambridge", "GPE", 0.9],
  ["Substitution Principle", "CONCEPT", "underpins", "Abstract Data Types", "CONCEPT", 0.79],
  ["Duck Typing", "CONCEPT", "generalises", "Abstract Data Types", "CONCEPT", 0.7],
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
