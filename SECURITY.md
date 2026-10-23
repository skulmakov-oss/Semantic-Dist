# Security Policy & Governance Model — Semantic-Dist

Status: Normative Repository Governance Authority  
Applies to: `skulmakov-oss/Semantic-Dist`

---

## 1. Governance Model

In this single-maintainer distribution repository, all changes follow a strict pull-request workflow enforced by GitHub branch protection and automated provenance verification:

1. **Pull Request Discipline**:
   - Every change enters `main` exclusively through a Pull Request.
   - Direct commits and direct pushes to `main` are prohibited.
   - Force pushes and branch deletion are prohibited.
   - Administrator bypass is disabled (`enforce_admins: true`).
   - Linear history is strictly enforced (squash/rebase only).

2. **Required CI Provenance Check**:
   - Every PR targeting `main` must pass the mandatory status check:
     `Verify Upstream Anchor Integrity` (job `verify-anchor-and-provenance` in `.github/workflows/verify-provenance.yml`).
   - This gate asserts the byte-for-byte cryptographic integrity of `upstream_anchor.json` against `manifests/anchor_schema.json` and verifies the exact pinned upstream Git commit SHA, raw `Cargo.lock` blob SHA-256 digest, and Git blob OID against `skulmakov-oss/Semantic`.

3. **Owner Merge & Authority**:
   - In GitHub, PR authors cannot approve their own PRs.
   - The repository owner (`skulmakov-oss`) decides when an eligible PR is merged after verifying CI pass, security posture, and code diff.
   - External or agent contributions submitted via PR require owner review before merging.

4. **Workflow & Dependency Governance**:
   - Workflow (`.github/workflows/**`) and packaging dependency changes require deliberate inspection by the owner.
   - Actions must be pinned to immutable commit SHAs.
   - Python validation dependencies must remain reproducibly hash-locked (`ci/requirements.txt`).
   - Candidate PR workflows receive read-only permissions (`contents: read`).
   - Packaging PRs do not receive signing certificates or publication credentials.

5. **Release Publication Authority**:
   - Release tags and release artifact publication require separate, explicit `OWNER PUBLISH GO`.
   - Release signing secrets are isolated and restricted to protected release environments.

6. **Compiler & Runtime Boundary**:
   - Upstream compiler, VM, and verifier sources belong exclusively to `skulmakov-oss/Semantic` and are never duplicated, vendored, or modified inside `Semantic-Dist`.
