# Observations (probe record)

Exact commands and results behind the "observed" statements in [language.md](language.md). Tool: public rc.2 portable `smc.exe`, source fingerprint `4dfa17a48b77e39f`. Inputs: `examples/qualification/ssf11` of the Semantic tag [`v1.3.0-rc.2`](https://github.com/skulmakov-oss/Semantic/tree/v1.3.0-rc.2/examples/qualification/ssf11). Paths are relative to that folder. Long output is shortened.

## Projects and packages
| Probe | Command | Exit | Output |
|---|---|---|---|
| `ch2.check_project` | `smc.exe check f06_project` | 0 | smc check passed: 0 warning(s), 0 scheduled law(s) |
| `ch2.run_project` | `smc.exe run f06_project` | 0 | (no output) |
| `ch2.test_project` | `smc.exe test f06_project` | 0 | ok tests/double.sm test result: ok. 1 passed |
| `ch2.run_packages` | `smc.exe run f06_packages/app` | 0 | (no output) |
| `ch2.package_inspect` | `smc.exe package inspect f06_packages/app` | 0 | {   "fingerprint_algorithm": "fnv1a64-non-cryptographic",   "graph_fingerprint": "fnv1a64:afddee7547fe317f",   "packages": [     {       "ca |
| `ch2.neg_missing_dep` | `smc.exe run f06_package_missing_dep` | 1 | package module admission error: dependency alias 'missing' expected Semantic.package at '…\does_not_exist\Semantic.package' (absolute path shortened) |
| `ch2.neg_entry_escape` | `smc.exe check f06_project_entry_escape` | 1 | failed to parse 'f06_project_entry_escape\semantic.toml': project entry '../main.sm' must not escape the project root |

## Capabilities (run in `f08_file_transform/sandbox`)
| Probe | Command | Exit | Output (audit lines omitted) |
|---|---|---|---|
| `ch3.transform_ok` | `smc.exe run ../main.sm --profile cli-file-transform --root . -- input.txt output.txt` | 0 | transform complete |
| `ch3.neg_read_only` | `smc.exe run ../main.sm --profile cli-read-only --root . -- input.txt output2.txt` | 1 | capability FsWrite denied for FsWrite [prom.cap.manifest v1 MissingCapability]: manifest does not grant this capability |
| `ch3.neg_escape` | `smc.exe run ../main.sm --profile cli-file-transform --root . -- input.txt ../escaped.txt` | 1 | ABI FsWrite failure [InvalidInput]: path must be relative and must not contain parent traversal |
| `ch3.neg_pure` | `smc.exe run ../main.sm --profile pure --root . -- input.txt output3.txt` | 1 | capability ArgsRead denied for ArgsRead [prom.cap.manifest v1 MissingCapability]: manifest does not grant this capability |

Afterwards the folder holds only `main.sm`, `sandbox/input.txt` and `sandbox/output.txt`.

## Artifacts and diagnostics
| Probe | Command | Exit | Output |
|---|---|---|---|
| `ch4.compile` | `smc.exe compile f01_minimal/main.sm -o minimal.smc` | 0 | compiled 'f01_minimal/main.sm' -> 'minimal.smc' (127 bytes) |
| `ch4.verify` | `smc.exe verify minimal.smc` | 0 | verified 'minimal.smc' (1 function(s), header=SEMCOD22, epoch=0.23) |
| `ch4.hash` | `smc.exe artifact hash minimal.smc` | 0 | sha256:4ca8a7ec7ebf776cbec3b97c1896b783b933ff31f69dc077e0396dad1cdde075 |
| `ch4.run_smc` | `smc.exe run-smc minimal.smc` | 0 | (no output) |
| `ch4.neg_wrong_hash` | `smc.exe run-smc minimal.smc --expect-sha256 sha256:0000000000000000000000000000000000000000000000000000000000000000 --profile pure --root .` | 1 | artifact identity mismatch: expected sha256:0000000000000000000000000000000000000000000000000000000000000000, found sha256:4ca8a7ec7ebf776cb |
| `ch4.neg_unsupported_header` | `smc.exe verify f09_verifier_rejection/unsupported_header.smc` | 1 | verify error [UnsupportedVersion] @0x0000: unsupported SemCode header 'NOTSEMCO' |
| `ch5.check_json` | `smc.exe check f02_quad_bare_condition/main.sm --format json` | 1 | {   "schema": "semantic.diagnostics",   "schema_version": 1,   "status": "failed",   "sources": [     {       "index": 0,       "path": "f02 |
| `ch5.explain` | `smc.exe explain E0201` | 0 | E0201: Type mismatch. Example: expected QVec/Bool, found other type. |
| `ch5.assertion` | `smc.exe run f10_runtime_failure/assertion_failure.sm` | 1 | assertion failed |
| `ch5.div_zero` | `smc.exe run f10_runtime_failure/division_by_zero.sm` | 1 | runtime trap: DivisionByZero |
| `ch5.step_quota` | `smc.exe run f10_runtime_failure/step_quota.sm` | 1 | quota exceeded: Steps limit=100000 used=100001 |

## Frozen C1 (`semantic-selfhost-compiler-C1.smc`, sha256 `2bfd56e1…`)
Command: `smc.exe run-smc semantic-selfhost-compiler-C1.smc --expect-sha256 sha256:2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --profile cli-read-only --root . --envelope trusted-compiler --max-steps 150000000 --max-calls 2000000 --max-frames 256 -- prog.sm`

| `prog.sm` | C1 result | sha256 of C1 output = `smc compile` output |
|---|---|---|
| 02_let | exit 0, `hex` line | equal (`1d604dc16333…`) |
| 03_fn | exit 0, `hex` line | equal (`054ac800ac66…`) |
| 06_quad | exit 0, `hex` line | equal (`aa321f5f8024…`) |
| 07_quad_match | exit 0, `hex` line | equal (`853681f64924…`) |
| 08_option | exit 0, `hex` line | equal (`fcf4beb02c8a…`) |
| 09_record | exit 0, `hex` line | equal (`613530e41afd…`) |
| file transform (capability calls) | exit 0, `error name @153: unknown function 'fs_write_text'` | — |
| project with `Import` | exit 0, `error unsupported @0: unsupported import form` | — |

The six `prog.sm` programs are: `let`/`let mut`; a two-function program; `quad` comparison; `quad` `match` with `_`; `Option` `match`; a `record`. Their sources are the first-chapter examples of the user manual (`docs/manual/01_first_programs.md`).
