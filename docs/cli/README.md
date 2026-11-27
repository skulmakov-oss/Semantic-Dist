# CLI reference (`smc` and `svm`, v1.3.0-rc.2)

**Status:** reference draft, non-normative. Normative source: [`docs/spec/cli.md` at tag v1.3.0-rc.2](https://github.com/skulmakov-oss/Semantic/blob/v1.3.0-rc.2/docs/spec/cli.md). Tool: public rc.2 portable `smc.exe`/`svm.exe`, source fingerprint `4dfa17a48b77e39f`.

- **Observed:** the command was run with the public rc.2 binary while preparing these docs. This is the observed behaviour of that binary, not formal qualification.
- **Not run here:** listed by `smc --help` or `cli.md`, but not executed.

## Exit codes
Normative (cli.md): `smc` commands follow one convention: **0 on success, 1 on error**; details are carried in the error text. Every failure measured for the user manual exited 1.

`smc run-smc` reports the **program's** outcome. A program that prints a rejection message and returns normally still exits 0. For the frozen self-hosted compiler, read its `hex …` / `error …` result line (see the user manual, chapter 6).

## Commands
| Group | Syntax | Verification |
|---|---|---|
| Identity | `smc version [--json]` | observed (fingerprint `4dfa17a4`, toolchain_version `0.1.0`) |
| Identity | `smc features` | observed: `enabled: std, profile-rust, profile-logos, debug-symbols` / `disabled: simd, bench` |
| Identity | `smc language describe --format json` | observed: schema `semantic.language-surface` v1, 14 features |
| Check | `smc check <input.sm\|project-root> [--format human\|json] [--deny …] [--metrics]` | observed (human and json) |
| Check | `smc lint <input.sm>` | observed: `lint passed: no warnings` |
| Check | `smc fmt [--check] <path>` | observed with `--check`; formatting without `--check` not run here |
| Build | `smc compile <input.sm\|project-root> -o <out.smc> [--profile auto\|rust] [--opt-level O0\|O1] [--debug-symbols]` | observed (default options) |
| Build | `smc hash-ast` / `hash-ir` / `hash-smc <input>` | observed for `hash-ast`, `hash-smc`; `hash-ir` not run here |
| Build | `smc dump-ast` / `dump-ir` / `dump-bytecode <input.sm>` | observed for `dump-ast`; others not run here |
| Artifact | `smc verify <input.smc\|project-root>` | observed |
| Artifact | `smc artifact hash <path.smc> [--json]` / `smc artifact inspect <path.smc> [--json]` | observed (text output) |
| Artifact | `smc disasm <input.smc>` | observed |
| Artifact | `smc migrate <check\|preview> <path> [--json] [--dry-run]` | not run here |
| Run | `smc run <input.sm\|project-root>` | observed |
| Run | `smc run <input> --profile <pure\|cli-read-only\|cli-file-transform> --root <dir> [-- args…]` | observed (all three profiles) |
| Run | `smc run-smc <input.smc>` | observed |
| Run | `smc run-smc <input.smc> --expect-sha256 <sha256:hex> --profile … --root … [--envelope verified-local\|trusted-compiler] [--max-steps N] [--max-calls N] [--max-frames N] [--metrics json] [-- args…]` | observed (from cli.md; **not printed by `smc --help`**) |
| Projects | `smc test <project-root>` | observed |
| Projects | `smc package inspect <project-root>` | observed |
| Diagnostics | `smc explain <error-code\|--list>` | observed |
| Interactive | `smc watch`, `smc repl`, `smc lsp [--stdio]` | not run here (interactive) |
| Other | `smc snapshots [--update]`, `smc work …`, `smc look ui frame …`, `smc hub …` | not run here |
| VM | `svm run <input.smc>` / `svm disasm <input.smc>` | observed; `svm --help` prints usage and exits 1 |

## Contract-sensitive commands (cli.md)
`smc compile`, `smc verify`, `smc test`, `smc run-smc`, `smc features`, `smc language describe --format json`.

## Not in the current surface (cli.md)
`smc doctor`, `smc profile show|train|validate`. Observed: the rc.2 binary answers `unknown command`, which matches the specification.

## Source profiles
Only the Rust-like profile reaches SemCode-producing and execution commands. The Logos profile is experimental and inspection-only (`dump-ast`, `dump-ir --profile logos`, `hash-ir --profile logos`).
