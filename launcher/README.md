# Safe Native Launcher Architecture (`sm-launch`)

Status: Design Specification  
Language: Rust / Native C

---

## Purpose

`sm-launch` is a lightweight cross-platform binary wrapper installed alongside `smc` and `svm`. It serves as the primary OS entrypoint when a user double-clicks or shell-executes a `.sm` source file.

## Execution Sequence

```
[OS Invocation: sm-launch "path/to/source.sm"]
                        │
                        ▼
       [1. Parse & Normalize File Path]
       - UTF-8 / Unicode handling
       - Resolve canonical absolute path
                        │
                        ▼
       [2. Inspect Origin Security Context]
       - Windows: Check Zone.Identifier ADS == 3 (Internet)
       - macOS: Check com.apple.quarantine
       - If Remote:
           Prompt user: "File downloaded from internet. Execute? [y/N]"
           If user declines -> Exit with code 2
                        │
                        ▼
       [3. Interactive Console Attachment]
       - If running without parent console (GUI spawn):
           Allocate new terminal console window
                        │
                        ▼
       [4. Verifier Admission Gate]
       - Execute: smc compile --verify-only "path/to/source.sm"
       - If compile or verification fails:
           Print diagnostic in red ANSI
           Hold terminal window ("Press any key to exit...")
           Exit with code 1
                        │
                        ▼
       [5. Deterministic Execution]
       - Execute: svm run-smc "path/to/source.smc"
       - Capture stdout/stderr
                        │
                        ▼
       [6. Completion Hold]
       - If GUI allocated: Wait for user keypress before window close
```
