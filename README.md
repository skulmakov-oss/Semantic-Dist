# Semantic-Dist — Native Distribution Packaging & Installer Foundation

Repository: `skulmakov-oss/Semantic-Dist`  
Authoritative Compiler Repository: `skulmakov-oss/Semantic`  
Upstream Pinned SHA: `1d1e76c7509a03baa0133abaaa5819f5d32582b2`  
Release Target: `v1.3.0-beta.1`

---

## Overview

`Semantic-Dist` is the independent native distribution and installer repository for the Semantic Language.

### Developer Preview: Windows x64 Installer
The Windows x64 installer (`Semantic-Setup-x64.exe`) provides a complete, self-contained Semantic environment:
- **Zero Toolchain Dependencies**: Users run Semantic without installing Rust, Cargo, Visual Studio, or Python.
- **Included Executables**:
  - `smc.exe` — Semantic Compiler CLI (`smc version`, `smc check`, `smc run`).
  - `svm.exe` — Semantic Deterministic Virtual Machine CLI (`svm run`).
  - `sm-launch.exe` — Safe native Windows launcher for terminal and Explorer execution.
- **Per-User Setup**: Installs to `%LOCALAPPDATA%\Programs\Semantic` without requiring administrator privileges.
- **File Association**: Associates `.sm` files with `sm-launch.exe` (`Semantic.SourceFile.1`).
- **Optional PATH integration**: Adds `Semantic\bin` to the user's `PATH`.

### What this installer contains — and what it does not
- **It contains:** the Rust toolchain built from the pinned upstream commit `1d1e76c7` (`smc`, `svm`) and the `sm-launch` launcher.
- **It does not contain:** the **self-hosted compiler**. That compiler is written in Semantic and reached a byte-identical `C1 = C2 = C3` fixed point on 2026-11-25. It is developed and qualified in [Semantic-Language](https://github.com/skulmakov-oss/Semantic-Language), and its Bootstrap Seal is validated, not reproduced or accepted.
- **Default compiler:** the installed `smc` remains the Rust reference compiler. Nothing in this package replaces it.

### Known issue (upstream)
A VM liveness regression in `skulmakov-oss/Semantic` (`aff35531`, included in the pinned `1d1e76c7`) affects this preview:
- **Effect:** a program admitted by `smc verify` can stop at run time with `read uninitialized reg rN` after a call to a function whose result is discarded. It fails closed; no wrong value was observed.
- **Not affected:** v1.2.0.
- **Fix:** [skulmakov-oss/Semantic#2087](https://github.com/skulmakov-oss/Semantic/pull/2087). A packaging update needs a new upstream pin under this repository's release policy.

### Running Semantic Programs
From PowerShell or CMD:
```powershell
smc run hello.sm
# or using the launcher:
sm-launch hello.sm
```

From Windows Explorer:
Double-click any `.sm` file. The launcher will ask for confirmation (especially if downloaded from the web) and execute the program in a visible console.

### Uninstallation
Uninstall via **Windows Settings -> Installed Apps** (or `Control Panel -> Programs and Features`), or directly by running `unins000.exe` in the Semantic installation folder. Registry entries and PATH modifications are cleanly reverted. User source files are never deleted.
