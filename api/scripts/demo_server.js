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
  ["Anders Hejlsberg", "PERSON", "created", "TypeScript", "SOFTWARE", 0.97],
  ["Anders Hejlsberg", "PERSON", "created", "C#", "SOFTWARE", 0.96],
  ["Brendan Eich", "PERSON", "created", "JavaScript", "SOFTWARE", 0.98],
  ["Graydon Hoare", "PERSON", "created", "Rust", "SOFTWARE", 0.97],
  ["Chris Lattner", "PERSON", "created", "Swift", "SOFTWARE", 0.96],
  ["Chris Lattner", "PERSON", "created", "LLVM", "SOFTWARE", 0.98],
  ["Rob Pike", "PERSON", "created", "Go", "SOFTWARE", 0.95],
  ["Ken Thompson", "PERSON", "created", "Go", "SOFTWARE", 0.94],
  ["Ken Thompson", "PERSON", "created", "C", "SOFTWARE", 0.93],
  ["Bjarne Stroustrup", "PERSON", "created", "C++", "SOFTWARE", 0.98],
  ["Rich Hickey", "PERSON", "created", "Clojure", "SOFTWARE", 0.97],
  ["Yukihiro Matsumoto", "PERSON", "created", "Ruby", "SOFTWARE", 0.97],
  ["John McCarthy", "PERSON", "created", "Lisp", "SOFTWARE", 0.98],
  ["Alan Kay", "PERSON", "created", "Smalltalk", "SOFTWARE", 0.96],
  ["Robin Milner", "PERSON", "created", "ML", "SOFTWARE", 0.97],
  ["Simon Peyton Jones", "PERSON", "maintains", "Haskell", "SOFTWARE", 0.95],
  ["James Gosling", "PERSON", "created", "Java", "SOFTWARE", 0.98],
  ["Barbara Liskov", "PERSON", "created", "CLU", "SOFTWARE", 0.9],
  ["Guido van Rossum", "PERSON", "worked at", "Dropbox", "ORG", 0.91],
  ["Anders Hejlsberg", "PERSON", "works at", "Microsoft", "ORG", 0.95],
  ["Brendan Eich", "PERSON", "co-founded", "Mozilla", "ORG", 0.94],
  ["Chris Lattner", "PERSON", "worked at", "Apple", "ORG", 0.93],
  ["Rob Pike", "PERSON", "worked at", "Google", "ORG", 0.94],
  ["Ken Thompson", "PERSON", "worked at", "Bell Labs", "ORG", 0.96],
  ["Barbara Liskov", "PERSON", "worked at", "MIT", "ORG", 0.93],
  ["John McCarthy", "PERSON", "worked at", "MIT", "ORG", 0.92],
  ["Alan Kay", "PERSON", "worked at", "Xerox PARC", "ORG", 0.95],
  ["Simon Peyton Jones", "PERSON", "worked at", "Microsoft", "ORG", 0.9],
  ["Robin Milner", "PERSON", "worked at", "Edinburgh", "ORG", 0.89],
  ["James Gosling", "PERSON", "worked at", "Sun Microsystems", "ORG", 0.94],
  ["Microsoft", "ORG", "maintains", "TypeScript", "SOFTWARE", 0.96],
  ["Microsoft", "ORG", "maintains", "C#", "SOFTWARE", 0.95],
  ["Mozilla", "ORG", "maintains", "Rust", "SOFTWARE", 0.86],
  ["Apple", "ORG", "maintains", "Swift", "SOFTWARE", 0.95],
  ["Google", "ORG", "maintains", "Go", "SOFTWARE", 0.95],
  ["Google", "ORG", "maintains", "Kotlin", "SOFTWARE", 0.72],
  ["JetBrains", "ORG", "created", "Kotlin", "SOFTWARE", 0.96],
  ["Bell Labs", "ORG", "produced", "C", "SOFTWARE", 0.94],
  ["Xerox PARC", "ORG", "produced", "Smalltalk", "SOFTWARE", 0.93],
  ["Sun Microsystems", "ORG", "produced", "Java", "SOFTWARE", 0.95],
  ["MIT", "ORG", "produced", "CLU", "SOFTWARE", 0.85],
  ["Microsoft", "ORG", "headquartered in", "Redmond", "GPE", 0.93],
  ["Apple", "ORG", "headquartered in", "Cupertino", "GPE", 0.94],
  ["Google", "ORG", "headquartered in", "Mountain View", "GPE", 0.93],
  ["MIT", "ORG", "headquartered in", "Cambridge", "GPE", 0.9],
  ["Bell Labs", "ORG", "headquartered in", "Murray Hill", "GPE", 0.88],
  ["C", "SOFTWARE", "influenced", "C++", "SOFTWARE", 0.95],
  ["C++", "SOFTWARE", "influenced", "Java", "SOFTWARE", 0.9],
  ["C++", "SOFTWARE", "influenced", "Rust", "SOFTWARE", 0.83],
  ["Java", "SOFTWARE", "influenced", "C#", "SOFTWARE", 0.89],
  ["Java", "SOFTWARE", "influenced", "Kotlin", "SOFTWARE", 0.92],
  ["JavaScript", "SOFTWARE", "influenced", "TypeScript", "SOFTWARE", 0.97],
  ["Python", "SOFTWARE", "influenced", "Ruby", "SOFTWARE", 0.71],
  ["Lisp", "SOFTWARE", "influenced", "Clojure", "SOFTWARE", 0.96],
  ["Lisp", "SOFTWARE", "influenced", "ML", "SOFTWARE", 0.78],
  ["ML", "SOFTWARE", "influenced", "Haskell", "SOFTWARE", 0.93],
  ["ML", "SOFTWARE", "influenced", "Rust", "SOFTWARE", 0.74],
  ["ML", "SOFTWARE", "influenced", "Scala", "SOFTWARE", 0.85],
  ["Haskell", "SOFTWARE", "influenced", "Scala", "SOFTWARE", 0.82],
  ["Haskell", "SOFTWARE", "influenced", "Swift", "SOFTWARE", 0.7],
  ["Smalltalk", "SOFTWARE", "influenced", "Ruby", "SOFTWARE", 0.86],
  ["Smalltalk", "SOFTWARE", "influenced", "Java", "SOFTWARE", 0.72],
  ["CLU", "SOFTWARE", "influenced", "Java", "SOFTWARE", 0.76],
  ["Rust", "SOFTWARE", "influenced", "Swift", "SOFTWARE", 0.68],
  ["TypeScript", "SOFTWARE", "compiles to", "JavaScript", "SOFTWARE", 0.99],
  ["Swift", "SOFTWARE", "compiles with", "LLVM", "SOFTWARE", 0.93],
  ["Rust", "SOFTWARE", "compiles with", "LLVM", "SOFTWARE", 0.94],
  ["Kotlin", "SOFTWARE", "runs on", "JVM", "SOFTWARE", 0.95],
  ["Scala", "SOFTWARE", "runs on", "JVM", "SOFTWARE", 0.95],
  ["Clojure", "SOFTWARE", "runs on", "JVM", "SOFTWARE", 0.93],
  ["Java", "SOFTWARE", "runs on", "JVM", "SOFTWARE", 0.97],
  ["TypeScript", "SOFTWARE", "implements", "Structural Typing", "CONCEPT", 0.9],
  ["TypeScript", "SOFTWARE", "implements", "Gradual Typing", "CONCEPT", 0.91],
  ["TypeScript", "SOFTWARE", "implements", "Type Inference", "CONCEPT", 0.88],
  ["Python", "SOFTWARE", "implements", "Duck Typing", "CONCEPT", 0.88],
  ["Python", "SOFTWARE", "implements", "Gradual Typing", "CONCEPT", 0.84],
  ["Ruby", "SOFTWARE", "implements", "Duck Typing", "CONCEPT", 0.87],
  ["Haskell", "SOFTWARE", "implements", "Type Classes", "CONCEPT", 0.96],
  ["Haskell", "SOFTWARE", "implements", "Algebraic Data Types", "CONCEPT", 0.95],
  ["Haskell", "SOFTWARE", "implements", "Type Inference", "CONCEPT", 0.94],
  ["ML", "SOFTWARE", "implements", "Type Inference", "CONCEPT", 0.96],
  ["ML", "SOFTWARE", "implements", "Algebraic Data Types", "CONCEPT", 0.93],
  ["Rust", "SOFTWARE", "implements", "Algebraic Data Types", "CONCEPT", 0.9],
  ["Rust", "SOFTWARE", "implements", "Ownership", "CONCEPT", 0.95],
  ["Swift", "SOFTWARE", "implements", "Algebraic Data Types", "CONCEPT", 0.88],
  ["Java", "SOFTWARE", "implements", "Type Erasure", "CONCEPT", 0.91],
  ["Scala", "SOFTWARE", "implements", "Type Erasure", "CONCEPT", 0.87],
  ["Scala", "SOFTWARE", "implements", "Type Classes", "CONCEPT", 0.85],
  ["Go", "SOFTWARE", "implements", "Structural Typing", "CONCEPT", 0.86],
  ["Clojure", "SOFTWARE", "implements", "Dynamic Typing", "CONCEPT", 0.92],
  ["JavaScript", "SOFTWARE", "implements", "Dynamic Typing", "CONCEPT", 0.94],
  ["C++", "SOFTWARE", "implements", "Static Typing", "CONCEPT", 0.93],
  ["CLU", "SOFTWARE", "implements", "Abstract Data Types", "CONCEPT", 0.94],
  ["Static Typing", "CONCEPT", "contrasts with", "Dynamic Typing", "CONCEPT", 0.9],
  ["Gradual Typing", "CONCEPT", "bridges", "Static Typing", "CONCEPT", 0.87],
  ["Gradual Typing", "CONCEPT", "bridges", "Dynamic Typing", "CONCEPT", 0.86],
  ["Structural Typing", "CONCEPT", "contrasts with", "Nominal Typing", "CONCEPT", 0.85],
  ["Duck Typing", "CONCEPT", "generalises", "Structural Typing", "CONCEPT", 0.8],
  ["Duck Typing", "CONCEPT", "requires", "Dynamic Typing", "CONCEPT", 0.82],
  ["Type Inference", "CONCEPT", "enables", "Static Typing", "CONCEPT", 0.83],
  ["Type Classes", "CONCEPT", "generalises", "Nominal Typing", "CONCEPT", 0.7],
  ["Type Erasure", "CONCEPT", "weakens", "Static Typing", "CONCEPT", 0.75],
  ["Algebraic Data Types", "CONCEPT", "enables", "Pattern Matching", "CONCEPT", 0.92],
  ["Abstract Data Types", "CONCEPT", "underpins", "Nominal Typing", "CONCEPT", 0.71],
  ["Algebraic Data Types", "CONCEPT", "requires", "Static Typing", "CONCEPT", 0.78],
  ["Substitution Principle", "CONCEPT", "underpins", "Abstract Data Types", "CONCEPT", 0.79],
  ["Barbara Liskov", "PERSON", "formalised", "Substitution Principle", "CONCEPT", 0.95],
  ["Ownership", "CONCEPT", "enables", "Memory Safety", "CONCEPT", 0.93],
  ["Garbage Collection", "CONCEPT", "enables", "Memory Safety", "CONCEPT", 0.88],
  ["Java", "SOFTWARE", "implements", "Garbage Collection", "CONCEPT", 0.95],
  ["Go", "SOFTWARE", "implements", "Garbage Collection", "CONCEPT", 0.94],
  ["Clojure", "SOFTWARE", "implements", "Immutability", "CONCEPT", 0.93],
  ["Haskell", "SOFTWARE", "implements", "Immutability", "CONCEPT", 0.94],
  ["Immutability", "CONCEPT", "enables", "Concurrency", "CONCEPT", 0.85],
  ["Erlang", "SOFTWARE", "implements", "Message Passing", "CONCEPT", 0.96],
  ["Go", "SOFTWARE", "implements", "Message Passing", "CONCEPT", 0.9],
  ["Message Passing", "CONCEPT", "enables", "Concurrency", "CONCEPT", 0.89],
  ["Smalltalk", "SOFTWARE", "implements", "Message Passing", "CONCEPT", 0.91],
  ["Lisp", "SOFTWARE", "implements", "Higher Order Functions", "CONCEPT", 0.94],
  ["Haskell", "SOFTWARE", "implements", "Higher Order Functions", "CONCEPT", 0.96],
  ["Lambda Calculus", "CONCEPT", "underpins", "Higher Order Functions", "CONCEPT", 0.93],
  ["Lambda Calculus", "CONCEPT", "underpins", "Type Inference", "CONCEPT", 0.8],
  ["Rust", "SOFTWARE", "implements", "Pattern Matching", "CONCEPT", 0.92],
  ["Scala", "SOFTWARE", "implements", "Pattern Matching", "CONCEPT", 0.9],
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
