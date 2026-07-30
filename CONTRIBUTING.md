# Contributing to graphmind

Thanks for helping build graphmind. This document covers the workflow (fork,
branch, PR) and the engineering standards every change is reviewed against.
If you take one thing away: **small, tested, standards-compliant pull requests
merge fast; everything else bounces.**

## Ground rules

- Be direct and respectful in review — critique code, not people.
- No secrets, API keys, or credentials in code, ever. `.env` is gitignored from
  day one; `.env.example` documents names only.
- Every commit is authored and committed **as yourself**, under your own GitHub
  identity. Never commit under a tool's default identity or a bot account, and
  never add `Co-Authored-By` trailers for AI tools. If you use AI coding
  assistance, treat it like an IDE: you review, edit, test, and commit the work
  as your own.
- The contributor graph should show exactly the people who wrote the code.
  Nothing else.

## Development setup

You need Docker and nothing else to run the stack; you need Python 3.12+ and
Node.js 20+ to run the checks locally.

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/<you>/graphmind.git
cd graphmind
git remote add upstream https://github.com/abj360/graphmind.git

cp .env.example .env
docker compose -f docker/docker-compose.yml up --build

# Local dev tooling
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Workflow

1. **Pick or open an issue first.** Non-trivial changes start with a short
   issue describing the problem, not a PR out of nowhere. Bug reports should
   include reproduction steps and what you expected instead.
2. **Branch from `main`** using the naming convention
   `<type>/<short-description>`, e.g. `feat/regex-search`,
   `fix/graphml-escaping`, `test/loader-retries`.
3. **Push the branch to your fork** and open a PR against `main` on the
   upstream repo. Keep PRs small enough to review in one sitting; split large
   features into a stack of PRs.
4. **Peter merges PRs** (he owns `main` on this repo). Expect review comments
   within a couple of days; address them with follow-up commits on the same
   branch rather than force-pushing.
5. Releases are tagged by the maintainer. You do not need to bump versions.

## Commit standards

- Conventional commit prefixes: `feat`, `fix`, `perf`, `refactor`, `test`,
  `chore`, `docs`, `ci`, `style`. The message is a plain-language summary of
  the change, not a restatement of the diff.
- Small, atomic commits: one logical thing per commit, revertible on its own.
- Filler-free history is not required — `wip`-style fixups during a branch are
  normal. The PR itself is the reviewable unit.

## Engineering standards

These are enforced by review and CI. The full text lives in the team's
standards doc; the essentials:

### File headers (every Python/JS/TS file)

```python
#!/usr/bin/env python3
"""
chunker.py --- splits source documents into overlapping, sentence-aware chunks

Contains:
    ChunkConfig: sizing knobs for the chunking pass
    TextChunker.chunk(): splits one document into chunks
"""

import os

from third_party import Thing

from local_module import other_thing
```

Shebang first (`#!/usr/bin/env python3`, `#!/usr/bin/env node`,
`#!/usr/bin/env ts-node`), then a structured module docstring: one line of
`<filename> --- <role>`, then a `Contains:` block listing what the file
exposes. Imports follow: stdlib, blank line, third-party, blank line, local —
alphabetized within each group. JS/TS files use the JSDoc equivalent.

### Docstrings (every function, method, and class — no exceptions)

- Line 1 starts with a third-person verb ending in "s": `Creates`,
  `Validates`, `Resolves`, `Computes`. What it does, not how.
- `Args:` with one line per argument when it takes arguments; `Returns:` with a
  named result when it returns something meaningful; `Attributes:` on classes
  holding state. Omit sections that have nothing to say.
- If a docstring needs paragraphs, the function is probably doing too much.

### Comments

Code explains itself through naming and structure; comments are the exception.
Comment only what is genuinely non-obvious: a business rule, a workaround for a
library bug, a deliberate deviation, a magic constant with a real source. No
restatements, no commented-out dead code — git history is the archive.

### Formatting & linting

- Python: **Ruff** for linting and formatting. **mypy --strict** on
  `extract/`, `resolution/`, `load/`.
- JS/JSX: **ESLint + Prettier**. JSON/YAML/Markdown/CSS: Prettier.
- Line length 100, double quotes, no exceptions.
- All of it runs as pre-commit hooks and as CI gates — nothing merges that
  would not pass locally.

### Naming

`snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE`
constants, `snake_case.py` files in Python; `camelCase`/`kebab-case`/PascalCase
components in JS. Names say what a thing is or does — no `data`, `temp`,
`thing`, `x`. Booleans read as questions (`is_ready`, `has_citation`).

### Types

- Full type hints on every Python signature, arguments and return type. No
  `Any` unless there is genuinely no better option — and then a one-line
  comment says why.
- TypeScript/JS: `strict: true`, no unchecked non-null assertions without a
  justifying comment.

### Error handling

- Catch specific exceptions, never bare `except:` / empty `catch {}`.
- Fail closed, not open: a timeout or unexpected state blocks/rejects rather
  than silently passing.
- Log errors with enough context to debug without reproducing locally.
- Never swallow an exception to make a red test green — fix the cause.

### Structure & design

- One responsibility per function (~30-line ceiling), one concern per file, no
  god objects. If a module does ingestion, scoring, and routing, split it.
- Composition over inheritance; dependency injection over global state; small,
  explicit interfaces.
- Prefer immutable data (frozen dataclasses/pydantic models) — most of our
  historical concurrency bugs came from mutable shared state.

## Testing requirements

- **New logic ships with tests in the same PR.** No "add tests later" tickets.
- Tests live next to what they test (`tests/unit`, `tests/integration` mirror
  the source tree).
- A test must be able to fail: assert on real behavior. Mocked dependencies
  (fake LLM client, recording Neo4j driver) are scripted doubles that can
  return failures.
- Python: `pytest tests/unit -q` runs fully offline; integration tests skip
  live-Neo4j cases unless `GRAPHMIND_TEST_NEO4J_URI` is set.
- API: `npm test` in `api/` runs the contract suite.

## Pre-merge checklist

Your PR should be able to answer yes to all of these (CI checks most of them):

- [ ] `ruff check .` and `ruff format --check .` clean; ESLint/Prettier clean
- [ ] `mypy --strict extract resolution load` clean
- [ ] Every new function/class has a verb-first docstring with
      Args/Returns/Attributes filled in where relevant
- [ ] No commented-out code; no restating-the-obvious comments
- [ ] Tests added alongside the change, and they can actually fail
- [ ] Commit authored and committed as you — your identity, no tool identity
- [ ] `docker compose -f docker/docker-compose.yml up --build` still boots the
      whole stack cleanly

## Where things live (and who reviews what)

| Area | Path | Default reviewer |
| --- | --- | --- |
| Extraction, prompts, ontology, inference | `extract/` | Peter |
| Entity resolution, alias table | `resolution/` | Angel |
| CDC, CI, Docker | `load/`, `.github/`, `docker/` | Angel |
| BFF, viewer, GraphML export | `api/`, `viz/` | Yannick |

CODEOWNERS routes review automatically; feel free to ask for a different
reviewer if the change spans areas.

## Asking questions

Open an issue with the `question` label for anything unclear — setup trouble,
design trade-offs, "is this behavior intended". For security-sensitive reports
(credentials, injection risks), do not open a public issue; contact the
maintainers privately first.
