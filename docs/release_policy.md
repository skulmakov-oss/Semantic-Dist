# Release Policy — Semantic-Dist

Status: Normative Release Authority  
Applies to: `skulmakov-oss/Semantic-Dist`

---

## 1. Release Versioning Axes

`Semantic-Dist` manages native packaging releases aligned with upstream compiler contracts:

| Axis | Version / Identifier | Description |
|---|---|---|
| **Product Release** | [`v1.3.0-rc.2`](https://github.com/skulmakov-oss/Semantic-Dist/releases/tag/v1.3.0-rc.2) (published prerelease, 2026-11-26, unsigned Windows x64 developer preview; previous candidate `v1.3.0-rc.1` at `fbb49594` was never published; previous preview `v1.3.0-beta.1`) | The external release tag and user-facing package version. |
| **Upstream Pinned SHA** | `98f9db199b28d6b126873f8f445aaff49b83d674` (integrated upstream main for rc.2) | The exact, immutable upstream commit of `skulmakov-oss/Semantic`. |
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
