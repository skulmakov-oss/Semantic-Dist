# Semantic-Dist — Agent Operating Contract

Status: Non-negotiable repository governance contract for AI agents in `skulmakov-oss/Semantic-Dist`

---

## 1. Scope & Authority Hierarchy

1. **Repository Owner explicit instruction**
2. **Normative Git-tracked documents (`SECURITY.md`, `README.md`, `upstream_anchor.json`)**
3. **Upstream contracts from `skulmakov-oss/Semantic` at exact pinned SHA**
4. **Local tests and build scripts**

This repository is **NOT** the compiler source repository. All compiler, parser, AST, IR, SemCode, verifier, and VM logic belong exclusively in `skulmakov-oss/Semantic`.

---

## 2. Agent Constraints & Boundaries

- **NO Upstream Mutations**: Agents operating in `Semantic-Dist` must NEVER modify `skulmakov-oss/Semantic` or claim authority over compiler semantics.
- **NO Direct Main Push**: All work proceeds on feature branches (`feat/*`, `fix/*`, `pkg/*`) via pull requests. Direct commits to `main` are strictly forbidden.
- **NO Self-Authorization**: Agents cannot authorize packaging merges, bypass branch protections, or publish releases without explicit `OWNER MERGE GO` and `OWNER PUBLISH GO`.
- **NO Invented Dependencies**: Do not introduce unvetted third-party crates or utilities into packaging workflows without explicit documentation and justification.
- **Stop on Drift**: If the upstream commit SHA or `Cargo.lock` digest mismatches `upstream_anchor.json`, STOP immediately and report the drift.
