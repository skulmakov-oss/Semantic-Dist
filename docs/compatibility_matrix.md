# Compatibility & Platform Support Matrix — Semantic-Dist

Status: Normative Platform Baseline  
Target Release: `v1.3.0-beta.1`

---

## 1. Operating System Support Matrix

| Platform | Architecture | Minimum Supported OS | Packaging Format | Runtime Dependency Strategy | Empirical Qualification Status |
|---|---|---|---|---|---|
| **Windows** | x86_64 (`x64`) | Windows 10 (Build 19041+) / Windows 11 | Inno Setup Executable (`.exe`) | Pure Win32 + statically linked MSVC CRT (`+crt-static`). No OpenBLAS dependency. | **UNVERIFIED** (Pending P2 build & clean VM test) |
| **Ubuntu Linux** | x86_64 (`amd64`) | Ubuntu 20.04 LTS / 22.04 LTS / 24.04 LTS | Debian Package (`.deb`) | Dynamically links `-lopenblas`. Declares `Depends: libc6 (>= 2.31), libopenblas0 (>= 0.3.8) \| libopenblas-base`. | **UNVERIFIED** (Pending P3 build & clean container test) |
| **macOS** | Apple Silicon (`aarch64`) | macOS 12 Monterey+ | Apple Installer (`.pkg`) | Bundled `libopenblas.0.dylib` in `/opt/semantic/lib/` with Mach-O `@rpath`. Signed & notarized. | **UNVERIFIED** (Pending P4 build & clean macOS runner test) |
| **macOS** | Intel (`x86_64`) | macOS 12 Monterey+ | Apple Installer (`.pkg`) | Bundled `libopenblas.0.dylib` in `/opt/semantic/lib/` with Mach-O `@rpath`. Signed & notarized. | **UNVERIFIED** (Pending P4 build & clean macOS runner test) |

---

## 2. Shell & File Association Support

| Platform | Shell Association | MIME / UTI Registration | Path Discovery | Default Action | Empirical Status |
|---|---|---|---|---|---|
| **Windows** | `HKCR\.sm` | `SemanticSourceFile` ProgID | User/System `PATH` via Registry | Interactive launch via `sm-launch.exe` | **UNVERIFIED** |
| **Ubuntu** | Freedesktop MIME | `text/x-semantic-source` | `/usr/bin/` | Interactive launch via `sm-launch` | **UNVERIFIED** |
| **macOS** | Uniform Type Identifier | `org.semantic-lang.source` | `/usr/local/bin/` | Terminal execution via `sm-launch` | **UNVERIFIED** |

---

## 3. Strict Verification Invariant

In accordance with Semantic project discipline:
- No installer or native package is claimed to exist until the artifact has been built, packaged, and executed on a pristine runner.
- The items marked **UNVERIFIED** above represent architectural requirements, not proven achievements.
