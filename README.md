# Semantic-Dist — Native Distribution Packaging & Installer Foundation

Repository: `skulmakov-oss/Semantic-Dist`  
Authoritative Compiler Repository: `skulmakov-oss/Semantic`  
Upstream Pinned SHA: `98f9db199b28d6b126873f8f445aaff49b83d674` (integrated upstream main for rc.2)  
Latest release: [`v1.3.0-rc.2`](https://github.com/skulmakov-oss/Semantic-Dist/releases/tag/v1.3.0-rc.2), a published prerelease and unsigned Windows x64 developer preview (`v1.3.0-rc.1` at `fbb49594` was never published; previous preview `v1.3.0-beta.1`)

---

**New here?** Read [docs/getting_started.md](docs/getting_started.md): repository roles, portable CLI, installer, source builds on the four qualified targets, and the self-hosted compiler.

## Quick start (portable CLI)
Download `semantic-language-windows-x64-v1.3.0-rc.2.zip` from the [release](https://github.com/skulmakov-oss/Semantic-Dist/releases/tag/v1.3.0-rc.2) and check it against `SHA256SUMS`. Then unzip it, open PowerShell in the folder, and save a `hello.sm`:
```
fn main() {
    let x: i32 = 40;
    assert(x + 2 == 42);
    return;
}
```
```powershell
.\smc.exe version                          # Source Fingerprint: 4dfa17a48b77e39f
.\smc.exe compile hello.sm -o hello.smc    # compiled 'hello.sm' -> 'hello.smc' (153 bytes)
.\smc.exe verify hello.smc
.\smc.exe run hello.sm                     # exit code 0
.\svm.exe run hello.smc                    # exit code 0
```
The binaries are unsigned. Install and uninstall are verified on GitHub-hosted runners only. Prebuilt binaries exist for Windows x64 only. See the release notes for every limitation.

---

## Overview

Status terms used in this repository (published, prerelease, qualified, validated, reproduced, accepted, stable) are defined in [docs/status_glossary.md](docs/status_glossary.md).


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
- **It contains:** the Rust toolchain (`smc`, `svm`) built from the pinned upstream commit (see Upstream Pinned SHA), plus the `sm-launch` launcher. That commit includes the VM liveness fix ([skulmakov-oss/Semantic#2087](https://github.com/skulmakov-oss/Semantic/pull/2087)).
- **It does not contain:** the **self-hosted compiler** (C1). The installed `smc` stays the default Rust compiler; this package does not replace it.
- **Self-hosted compiler:** written in Semantic and developed and qualified in [Semantic-Language](https://github.com/skulmakov-oss/Semantic-Language). Its Bootstrap Seal is validated, not reproduced or accepted.

### Optional: run the self-hosted compiler (C1)
The pinned identities are in [`manifests/selfhost_pin.json`](manifests/selfhost_pin.json): C1 SHA-256 `2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939`, 339,746 bytes.

1. Get C1 in either of two ways:
   - download `semantic-selfhost-compiler-C1.smc` from the [v1.3.0-rc.2 release](https://github.com/skulmakov-oss/Semantic-Dist/releases/tag/v1.3.0-rc.2) and check its SHA-256;
   - reproduce it from source: build `smc` at the C0 commit and run `smc compile compiler/main.sm -o C1.smc` in a Semantic-Language checkout at the pinned commit.
2. Run it with the installed `smc`. `--expect-sha256` binds the exact bytes, and the verifier admits C1 before it runs:
   ```powershell
   smc run-smc C1.smc --expect-sha256 sha256:2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 `
     --profile cli-read-only --root <folder with prog.sm> --envelope trusted-compiler `
     --max-steps 150000000 --max-calls 2000000 --max-frames 256 -- prog.sm
   ```
3. Read the result: the compiler prints the program's SemCode as a `hex` line, and `smc verify` admits it.

**Supported subset:** the Bootstrap Subset of Semantic-Language, not the full language. Platform: Windows x64 only.

**CI:** the build workflow reproduces C1 from source on a fresh hosted Windows runner, then:
- installs the package;
- checks that a wrong hash is rejected;
- compiles a program and compares the bytes with C0;
- verifies that C1 compiles its own source back to C1;
- uninstalls.

**Relation to the contract executor:** the Bootstrap Contract v4 normative executor is `skulmakov-oss/Semantic@825deca4`. It stays frozen and separate; this distribution runtime is the corrected upstream pin.

### Known issue in the earlier preview
`v1.3.0-beta.1` (pinned `1d1e76c7`) contains the VM liveness regression `aff35531`.
- **Effect:** a verified program can stop with `read uninitialized reg rN` after a call whose result is discarded. It fails closed.
- **Fix:** the `v1.3.0-rc.2` pin includes the fix. `v1.3.0-beta.1` is unchanged.

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
