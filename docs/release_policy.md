# Release Policy — Semantic-Dist

Status: Normative Release Authority  
Applies to: `skulmakov-oss/Semantic-Dist`

---

## 1. Release Versioning Axes

`Semantic-Dist` manages native packaging releases aligned with upstream compiler contracts:

| Axis | Version / Identifier | Description |
|---|---|---|
| **Product Release** | `v1.3.0-beta.1` | The external release tag and user-facing package version. |
| **Upstream Pinned SHA** | `1d1e76c7509a03baa0133abaaa5819f5d32582b2` | The exact, immutable upstream commit of `skulmakov-oss/Semantic`. |
| **Packaging Revision** | `dist.1` | Internal packaging iteration for installers sharing the same compiler SHA. |
| **SemCode Header** | `SEMCOD22` (rev 23) | Baseline bytecode format admitted by `sm-verify`. |

---

## 2. Release Publication Gate Protocol

Release publication cannot occur autonomously. It follows a strict 4-step protocol:

1. **Pre-flight Build & Verification**:
   - Upstream commit cloned and verified against `upstream_anchor.json`.
   - Toolchain and Cargo.lock validated.
   - Clean-machine test matrix passes on Windows, Ubuntu, and macOS.
2. **Provenance Attestation**:
   - `build_provenance.json` generated and sealed with SHA-256 digests.
3. **Owner Review & Authorization**:
   - Repository Owner reviews test artifacts and evidence.
   - Owner explicitly issues **`OWNER PUBLISH GO`**.
4. **Publication**:
   - Release workflow triggers in `Release-Publishing` GitHub environment.
   - Signed packages uploaded to GitHub Releases with attached checksums.
