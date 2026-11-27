# Semantic User Manual (v1.3.0-rc.2)

A practical guide for writing and running Semantic programs with the published `v1.3.0-rc.2` tools. It is a **tutorial**, not a specification.

- **Normative language rules:** the upstream specifications at the release tag, [docs/spec @ v1.3.0-rc.2](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/docs/spec). If this manual and the specification disagree, the specification wins.
- **Getting the tools:** [getting_started.md](../getting_started.md).

## Chapters
| # | Chapter | Status |
|---|---|---|
| 1 | [First programs](01_first_programs.md): values, functions, control flow, `quad`, `Option`, records, errors | draft; every example run with the public rc.2 `smc` |
| 2 | [Projects, imports and packages](02_projects.md) | draft; run (rc.2 tag examples) |
| 3 | [Capabilities and the host boundary](03_capabilities.md) | draft; run, including denials |
| 4 | [Artifacts: compile, verify, hash, run](04_artifacts.md) | draft; run |
| 5 | [Diagnostics and exit codes](05_diagnostics.md) | draft; run |
| 6 | [The self-hosted compiler (C1) and the Bootstrap Subset](06_selfhost_c1.md) | draft; run (fixed-point reproduction not run) |
| 7–10 | [Proposed: quad logic, collections, types, memory](next_sections.md) | planning only |

**Conventions:**
- Commands are PowerShell, run inside the folder where the rc.2 portable zip was extracted.
- Examples marked *run* were executed as shown. The output in the text is the actual output.
