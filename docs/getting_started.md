# Getting started with Semantic v1.3.0-rc.2

This is the single entry point for **using** Semantic. It covers:
- what each repository is for;
- how to get the published Windows x64 preview;
- how to build from source on the four qualified targets;
- how to run the frozen self-hosted compiler.

Every command below lists its verification. *Run* means it was executed exactly as written against the public rc.2 assets; the logs are kept with the documentation evidence. *Not run here* means the command is documented from CI or the upstream guides and was not executed for this page.

> **Status:** `v1.3.0-rc.2` is a **published prerelease**. It is an **unsigned Windows x64 developer preview**, **not** a stable release. The self-hosting Bootstrap Seal is **validated**, not independently reproduced and not accepted. The terms are defined in the upstream [public status model](https://github.com/skulmakov-oss/Semantic/blob/main/docs/roadmap/public_status_model.md) and in Semantic-Language [Bootstrap Contract v4 §10.9](https://github.com/skulmakov-oss/Semantic-Language/blob/main/docs/BOOTSTRAP_CONTRACT.md).

## 1. Which repository does what
| Repository | Responsibility | You go there for |
|---|---|---|
| [Semantic](https://github.com/skulmakov-oss/Semantic) | Language and SemCode authority: Rust reference compiler (`smc`), verifier, deterministic VM (`svm`) | the specification, building from source, issues about the language |
| [Semantic-Language](https://github.com/skulmakov-oss/Semantic-Language) | The compiler written in Semantic (`compiler/*.sm`) and its bootstrap qualification (Bootstrap Contract v4) | self-hosting, the C0 → C1 → C2 fixed point, Seal reproduction |
| **Semantic-Dist** (this repository) | Packaging: Windows installer, portable CLI, provenance, four-target qualification | downloading and installing a release |

## 2. Windows x64: portable CLI (no installer)
Assets: [v1.3.0-rc.2 release](https://github.com/skulmakov-oss/Semantic-Dist/releases/tag/v1.3.0-rc.2). **Verification: run** on Windows x64 in PowerShell 7.

```powershell
$base = "https://github.com/skulmakov-oss/Semantic-Dist/releases/download/v1.3.0-rc.2"
Invoke-WebRequest "$base/semantic-language-windows-x64-v1.3.0-rc.2.zip" -OutFile semantic-language-windows-x64-v1.3.0-rc.2.zip
Invoke-WebRequest "$base/SHA256SUMS" -OutFile SHA256SUMS
(Get-FileHash semantic-language-windows-x64-v1.3.0-rc.2.zip -Algorithm SHA256).Hash.ToLower()
# must equal the zip's line in SHA256SUMS:
# dbaa52714c44e45a309378c2560d692cc8dc60e950495f0e58d9701fe0acfcc3
Expand-Archive semantic-language-windows-x64-v1.3.0-rc.2.zip -DestinationPath semantic
Set-Location semantic
```

Save as `hello.sm`:
```
fn main() {
    let x: i32 = 40;
    assert(x + 2 == 42);
    return;
}
```

```powershell
.\smc.exe version                         # Source Fingerprint: 4dfa17a48b77e39f; Release Signing: unsigned
.\smc.exe compile hello.sm -o hello.smc   # compiled 'hello.sm' -> 'hello.smc' (153 bytes)
.\smc.exe verify hello.smc                # verified 'hello.smc' (1 function(s), header=SEMCOD22, epoch=0.23)
.\smc.exe run hello.sm                    # exit code 0
.\svm.exe run hello.smc                   # exit code 0
.\smc.exe artifact hash hello.smc         # sha256:3b1113fedd90ff0e9c8c4ca99123e35c3fe80c41e18aedf5dd66de16eda7a264
```

## 3. Windows x64: installer
`Semantic-Setup-x64.exe` installs `smc`, `svm` and `sm-launch` per user, under `%LOCALAPPDATA%\Programs\Semantic`. It can optionally add them to your user PATH. Uninstall from *Settings → Apps*.

**Verification: not run here.** The silent install, PATH registration, CLI smoke, self-host fixed point and uninstall are verified by the installer workflow on fresh GitHub-hosted Windows runners (release build run 45830812555). Interactive installs, clean consumer machines, upgrades and non-default Windows editions are **not** qualified. The installer is **unsigned**, so SmartScreen may warn.

## 4. Build from source (four qualified targets)
The runtime at tag `v1.3.0-rc.2` (`98f9db19`) passes the native test matrix with 0 failures on macOS arm64, Linux x86_64, Linux arm64 and Windows x64 ([Native Matrix run](https://github.com/skulmakov-oss/Semantic/actions/runs/45747674708)). 14 tests are `#[ignore]` on every target, and 2 file-system cases are reported as unsupported on macOS. **Prebuilt binaries exist only for Windows x64.**

Requirements: Git, `rustup` (the repository pins Rust 1.97.1), a C toolchain/linker. Use an **LF checkout**: a CRLF checkout changes the source fingerprint.

```bash
git -c core.autocrlf=false -c core.eol=lf clone --branch v1.3.0-rc.2 --depth 1 https://github.com/skulmakov-oss/Semantic.git Semantic
cd Semantic
git rev-parse HEAD            # 98f9db199b28d6b126873f8f445aaff49b83d674
cargo build --release --locked --bin smc --bin svm
./target/release/smc version  # Source Fingerprint: 4dfa17a48b77e39f
```

| Host | Extra step | Verification |
|---|---|---|
| Windows x64 (MSVC) | none | **Run** (Rust 1.97.1, release build about 4.5 min) |
| Linux x86_64 / arm64 | `sudo apt-get install -y libopenblas-dev` (Debian/Ubuntu) | **Not run here.** The same step is used by the CI matrix (ubuntu-24.04, ubuntu-24.04-arm) |
| macOS arm64 | the CI runner (macos-15) needs no extra step; other hosts may need `brew install openblas` | **Not run here.** The `brew` step is untested |

For the full developer walkthrough (examples, projects, packages, capabilities), see the upstream [Getting Started](https://github.com/skulmakov-oss/Semantic/blob/main/docs/getting_started.md). It describes current `main`, which is newer than this prerelease.

## 5. Run the frozen self-hosted compiler (C1)
`semantic-selfhost-compiler-C1.smc` is attached to the release: SHA-256 `2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939`, 339,746 bytes. **Verification: run** with the portable `smc` from section 2. Put `prog.sm` (for example the `hello.sm` above) into a folder `prog`, and download C1 next to the `semantic` folder:

```powershell
Invoke-WebRequest "$base/semantic-selfhost-compiler-C1.smc" -OutFile ..\semantic-selfhost-compiler-C1.smc
.\smc.exe run-smc ..\semantic-selfhost-compiler-C1.smc --expect-sha256 sha256:2bfd56e161c40c8f746b6fd6530560f55aa026df29e50a81b99ea5ee3da4e939 --profile cli-read-only --root prog --envelope trusted-compiler --max-steps 150000000 --max-calls 2000000 --max-frames 256 -- prog.sm
```

- **Output:** capability audit lines, then a `hex …` line with the compiled SemCode.
- **Checked behaviour:** decoded to bytes, `smc verify` admits the output, and `smc artifact hash` gives the same `sha256:3b1113fe…` as `smc compile` in section 2.
- **Negative check:** a wrong `--expect-sha256` is rejected with `artifact identity mismatch` and exit code 1.
- **Scope:** C1 supports the Bootstrap Subset of Semantic, not the full language.

## 6. Reproduce the self-hosting fixed point
- **Verification: not run here** (about 1–2 hours).
- **Instructions:** `REPRODUCTION_KIT.md` and `semantic-reproduction-kit-v2.1.zip` (release assets), and Semantic-Language [docs/selfhost/README.md](https://github.com/skulmakov-oss/Semantic-Language/blob/main/docs/selfhost/README.md).
- **What it requires:** you build C0 (`1d1e76c7`) and the executor (`825deca4`) from LF checkouts, then compare your C1/C2 identities.
- **What counts:** only a run **by a different operator on a different host** counts as a Seal *reproduction* (Bootstrap Contract v4 §10.9). A rerun by the producer is repeatability evidence.

## 7. Limitations of this release
1. **Unsigned:** no code signing on the installer or the binaries.
2. **Installer qualification:** CI-runner only; no clean-host qualification.
3. **Platforms:** Windows x64 binaries only; other targets are qualified when built from source.
4. **Reproducibility:** native binaries are not bit-reproducible. Identity = commit + source fingerprint + `build_provenance.json`.
5. **Dependency advisory:** open `lru` advisory (UI demo crates only; not in `smc`/`svm`/`sm-launch`).
6. **TOCTOU:** a path race in hub vector storage.
7. **Tests not run:** ignored and unsupported tests (section 4).
8. **Seal:** validated only; no independent reproduction or acceptance.
