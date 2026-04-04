# Integrating graphmind with retrieval-core

This document describes how the knowledge graph produced by graphmind is
queried as a **secondary retrieval path** from `retrieval-core`: when it
helps, how the query path is shaped, what the operational constraints
are, and how to run the whole thing locally.

Audience: engineers working on either repo. Familiarity with Cypher is
assumed at the "can read a MATCH" level.
