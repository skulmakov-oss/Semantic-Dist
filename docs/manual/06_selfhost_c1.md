# 6. The frozen self-hosted compiler (C1) and the Bootstrap Subset

`semantic-selfhost-compiler-C1.smc` (SHA-256 `2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939`, 339,746 bytes) is the compiler written in Semantic. C0 compiled it from the frozen source `S` under Bootstrap Contract v4. It is attached to the rc.2 release. Running it, as below, uses that frozen artifact; it does **not** requalify or change the Bootstrap.

## 6.1 Compiling a program with C1
From a folder that contains `prog.sm`:
```powershell
smc.exe run-smc semantic-selfhost-compiler-C1.smc --expect-sha256 sha256:2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --profile cli-read-only --root . --envelope trusted-compiler --max-steps 150000000 --max-calls 2000000 --max-frames 256 -- prog.sm
```
C1 prints capability audit lines, then either a `hex …` line (the compiled SemCode) or an `error …` line.

| Program | Result | Bytes vs `smc compile` |
|---|---|---|
| `02_let.sm` (chapter 1) | 0, `hex` line | byte-identical to `smc compile` |
| `03_fn.sm` (chapter 1) | 0, `hex` line | byte-identical to `smc compile` |
| `06_quad.sm` (chapter 1) | 0, `hex` line | byte-identical to `smc compile` |
| `07_quad_match.sm` (chapter 1) | 0, `hex` line | byte-identical to `smc compile` |
| `08_option.sm` (chapter 1) | 0, `hex` line | byte-identical to `smc compile` |
| `09_record.sm` (chapter 1) | 0, `hex` line | byte-identical to `smc compile` |

## 6.2 Outside the Bootstrap Subset
C1 accepts only the **Bootstrap Subset**: the minimum source subset needed to express the compiler itself ([BOOTSTRAP_SUBSET.md](https://github.com/skulmakov-oss/Semantic-Language/blob/main/docs/BOOTSTRAP_SUBSET.md)). Measured rejections:
| Program | Actual C1 output | `run-smc` exit |
|---|---|---|
| chapter 3 file transform | `error name @153: unknown function 'fs_write_text'` | 0 |
| chapter 2 project with `Import` | `error unsupported @0: unsupported import form` | 0 |

> **Important (observed):** when C1 rejects a program, the `run-smc` **process still exits 0**. The rejection is the `error …` line. Treat a missing `hex` line as failure; do not rely on the exit code. Use the Rust `smc` for the full language.

## 6.3 Status
- The C0 → C1 → C2 fixed point is qualified under Bootstrap Contract v4. CI runs on four targets are **repeatability evidence**.
- The Bootstrap Seal is **validated**, **not independently reproduced**, **not accepted** (see [status glossary](../status_glossary.md)).
- Prebuilt C1 runs wherever the published `smc` runs. Only Windows x64 binaries are published; on the other three targets build `smc` from source (getting started §4).
- Reproducing the fixed point takes about 1–2 hours and is **not run** here; see `REPRODUCTION_KIT.md` in the release.
