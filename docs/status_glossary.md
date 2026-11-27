# Status glossary

One vocabulary for Semantic, Semantic-Language and Semantic-Dist. It does **not** replace the normative sources; it maps to them:
- the upstream [public status model](https://github.com/skulmakov-oss/Semantic/blob/main/docs/roadmap/public_status_model.md), with four families: *Published Stable*, *Qualified Limited Release*, *Landed On `main`, Not Yet Promised*, *Out Of Scope*;
- the Bootstrap Seal states in [Bootstrap Contract v4 §10.9](https://github.com/skulmakov-oss/Semantic-Language/blob/main/docs/BOOTSTRAP_CONTRACT.md): *validated*, *reproduced*, *accepted*.

If this page and a normative source ever differ, the normative source wins.

| Term | Meaning | Normative anchor | Not the same as |
|---|---|---|---|
| **implemented** | Code exists on a branch or on `main` | public status model: *Landed On `main`, Not Yet Promised* (once on main) | qualified, released |
| **qualified** | Passed a named, reproducible qualification (test matrix, gates, differential corpus) at an exact commit, with recorded evidence | public status model: *Qualified Limited Release* (for the Gate 1 contour); otherwise the named run | published, stable |
| **published** | Artifacts released publicly under a tag (a prerelease or a stable release) | release object and tag | stable |
| **prerelease** | Published but marked as a prerelease; no stability promise | GitHub release flag | stable |
| **stable** | The published stable line with stability promises | public status model: *Published Stable* | prerelease, qualified |
| **validated** (Seal) | The bootstrap evidence record passes `check_evidence` | §10.9 | reproduced |
| **reproduced** (Seal) | A distinct operator on a distinct host, from the same C0 and `S`, reports identical C0, source-set, C1 and C2 identities and comparison result | §10.9 | a rerun by the producer (*repeatability evidence*) |
| **independently reproduced** | Used here only as a synonym of Seal **reproduced** (distinct operator **and** distinct host) | §10.9 | CI or integrator runs operated by the producer |
| **accepted** (Seal) | The owner accepted the reproduced Seal | §10.9 | validated, reproduced |
| **repeatability evidence** | The same result again from the same operator: another host, another run, or CI | §10.9 ("not a reproduction") | reproduced |

## Where things stand (2026-11-27)
| Item | Status |
|---|---|
| `v1.3.0-rc.2` (Semantic-Dist) | **published prerelease**; unsigned Windows x64 developer preview; not stable |
| Runtime at `98f9db19` | **qualified**: native test matrix on 4 targets, 0 failures (14 ignored, 2 macOS unsupported) |
| Prebuilt binaries | **published** for Windows x64 only |
| Installer | install/uninstall verified on hosted CI runners only (no clean-host qualification) |
| Self-hosting fixed point (C1 = C2 = C3, `2bfd56e1`) | **qualified** under Bootstrap Contract v4. The four-target CI runs are **repeatability evidence** |
| Bootstrap Seal | **validated**; **not reproduced**, **not accepted** |
| Semantic `main` after `98f9db19` | **Landed On `main`, Not Yet Promised**. Not part of rc.2 |
| Latest **stable** | Semantic [v1.2.0](https://github.com/skulmakov-oss/Semantic/releases/tag/v1.2.0) (Windows x64, unsigned, explicit limits) |
