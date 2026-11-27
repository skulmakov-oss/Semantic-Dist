# Semantic User Manual (v1.3.0-rc.2)

A practical guide for writing and running Semantic programs with the published `v1.3.0-rc.2` tools. It is a **tutorial**, not a specification.

- **Normative language rules:** the upstream specifications at the release tag, [docs/spec @ v1.3.0-rc.2](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/docs/spec). If this manual and the specification disagree, the specification wins.
- **Getting the tools:** [getting_started.md](../getting_started.md).

## Chapters
| # | Chapter | Status |
|---|---|---|
| 1 | [First programs](01_first_programs.md): values, functions, control flow, `quad`, `Option`, records, errors | draft; every example run with the public rc.2 `smc` |
| 2 | Projects and imports (`smc` project roots, modules) | planned |
| 3 | Capabilities and the host boundary (file read/write, stdout, profiles) | planned |
| 4 | Artifacts: compile, verify, hash, `run-smc --expect-sha256` | planned |
| 5 | Diagnostics and error codes | planned; will reference docs/ERROR_CODES.md |
| 6 | The self-hosted compiler (C1) and the Bootstrap Subset | planned |

**Conventions:**
- Commands are PowerShell, run inside the folder where the rc.2 portable zip was extracted.
- Examples marked *run* were executed as shown. The output in the text is the actual output.
