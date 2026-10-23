# Native Launcher (`sm-launch.exe`)

The Native Launcher provides safe, single-click and command-line execution of `.sm` Semantic source files on Windows.

## Canonical Architecture

The launcher invokes the installed Semantic compiler using the canonical execution command:
```powershell
smc run <file.sm>
```
This command compiles, verifies (via `sm-verify`), and executes the program on the virtual machine in a single step without exposing or executing unverified bytecode.

## Security & Path Guarantees

1. **Local Compiler Resolution**:
   - `sm-launch.exe` resolves `smc.exe` strictly from its own installation directory (`{app}\bin`).
   - It **never** resolves `smc.exe` from the current working directory or ambient `PATH` entries.
2. **Path Sanitization**:
   - Accepts exactly one source file parameter.
   - Validates that the file exists, is not a directory, and has the `.sm` extension.
   - Supports long paths, whitespace, and Unicode file names.
3. **Double-Click & Download Protection**:
   - Detects execution from Windows Explorer (`GetConsoleProcessList`).
   - Inspects NTFS `Zone.Identifier` alternate data streams (files downloaded from untrusted internet origins).
   - Displays a native execution confirmation dialog before running untrusted or Explorer-launched scripts.
   - Keeps the console window open after completion when launched from Explorer, while running smoothly without pause when invoked from an existing terminal.
