# Semantic-Dist — Native Distribution Packaging & Installer Foundation

Repository: `skulmakov-oss/Semantic-Dist`  
Authoritative Compiler Repository: `skulmakov-oss/Semantic`  
Upstream Pinned SHA: `1d1e76c7509a03baa0133abaaa5819f5d32582b2`  
Release Target: `v1.3.0-beta.1`

---

## Overview

`Semantic-Dist` is the independent native distribution and installer repository for the Semantic Language. It produces signed, turnkey desktop and server packages for:

- **Windows x64**: `Semantic-Setup-x64.exe` (Native Setup Installer)
- **Ubuntu Linux amd64**: `semantic_1.3.0-beta.1_amd64.deb` (Debian Package)
- **macOS Apple Silicon & Intel**: `Semantic-1.3.0-beta.1-arm64.pkg` and `Semantic-1.3.0-beta.1-x86_64.pkg` (Native Apple Installers)

### Key Architectural Tenets:
1. **Zero External Toolchain Required**: Users run Semantic without installing Rust, Cargo, MSVC, Xcode, or Homebrew.
2. **Immutable Upstream Provenance**: All builds are pinned to an exact Git SHA of `skulmakov-oss/Semantic` recorded in `upstream_anchor.json`.
3. **No Code Duplication**: Compiler, parser, verifier, and VM logic live exclusively in `skulmakov-oss/Semantic`. `Semantic-Dist` only owns launchers, packaging scripts, installer manifests, and clean-machine qualification tests.
4. **Verifier-First Native Execution**: Launchers and file associations guarantee that `.sm` execution strictly passes verifier admission before reaching the VM.
5. **Untrusted Code Safeguards**: Files downloaded from remote origins (e.g. Zone.Identifier / Quarantine) require explicit user confirmation before execution.
