# Architecture Specification — Semantic-Dist

Status: Normative Architecture Document  
Applies to: `skulmakov-oss/Semantic-Dist`

---

## 1. System Topology & Separation of Concerns

`Semantic-Dist` decouples native distribution engineering from the core deterministic compiler repository.

```
┌─────────────────────────────────────────────────────────────┐
│ Upstream Authority: skulmakov-oss/Semantic                  │
│ Pinned SHA: 1d1e76c7509a03baa0133abaaa5819f5d32582b2        │
│ Contract: Pure, deterministic compiler & VM engine          │
│ Artifacts: smc, svm                                         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Cloned at immutable SHA
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Distribution Engine: skulmakov-oss/Semantic-Dist            │
│ Inputs: upstream_anchor.json, packaging templates, launcher │
│ Outputs: Native Installers (.exe, .deb, .pkg)               │
└──────────────────────────────┬──────────────────────────────┘
                               │ Verified & signed
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ End-User Systems (Windows, Ubuntu, macOS)                   │
│ UX: 1-click install, .sm file association, console display, │
│ untrusted code confirmation, verifier-first VM execution    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Package Architecture by Operating System

### 2.1 Windows x64 (`Semantic-Setup-x64.exe`)
- **Engine**: Inno Setup script (`packaging/windows/setup.iss`).
- **Installed Components**:
  - `bin\smc.exe`: Semantic Compiler CLI.
  - `bin\svm.exe`: Semantic Virtual Machine.
  - `bin\sm-launch.exe`: Native Launcher wrapper.
  - `docs\`: Normative contracts and licenses.
- **Shell Integrations**:
  - Registers ProgID `Semantic.SourceFile.1`.
  - Maps `.sm` extension to `sm-launch.exe "%1"`.
  - Prepends `bin\` to user `PATH`.
  - Installs Windows Add/Remove Programs uninstaller registry keys.

### 2.2 Ubuntu Linux amd64 (`semantic_1.3.0-beta.1_amd64.deb`)
- **Format**: Standard Debian package (`dpkg-deb`).
- **Dependencies**: `libc6 (>= 2.31), libopenblas0 (>= 0.3.8) | libopenblas-base`.
- **Filesystem Mapping**:
  - `/usr/bin/smc` $\rightarrow$ CLI binary.
  - `/usr/bin/svm` $\rightarrow$ VM binary.
  - `/usr/bin/sm-launch` $\rightarrow$ Launcher script.
  - `/usr/share/mime/packages/semantic.xml` $\rightarrow$ MIME type `text/x-semantic-source`.
  - `/usr/share/applications/semantic.desktop` $\rightarrow$ Desktop launcher entry.

### 2.3 macOS Apple Silicon & Intel (`Semantic-1.3.0-beta.1-*.pkg`)
- **Format**: Apple Component Package (`pkgbuild` & `productbuild`).
- **Runtime Library Bundling**:
  - Bundles `libopenblas.0.dylib` in `/opt/semantic/lib/`.
  - Updates `@rpath` on `smc` and `svm` using `install_name_tool`.
- **System Integrations**:
  - Symlinks `/opt/semantic/bin/smc` and `svm` into `/usr/local/bin`.
  - Registers UTI `org.semantic-lang.source` for `.sm`.
