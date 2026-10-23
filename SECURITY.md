# Security & Governance Policy — Semantic-Dist

Status: Normative Repository Governance Authority  
Applies to: `skulmakov-oss/Semantic-Dist`

---

## 1. Governance Model for Sole-Owner Repository

In GitHub, a pull request author **cannot approve their own pull request**. In a single-maintainer repository where the repository owner authors PRs or directs agent contributions:

1. **Owner Authority**:
   - Explicit owner authorization is documented directly in the issue/PR discussion thread as a formal governance record (`OWNER MERGE GO`, `OWNER PUBLISH GO`).
2. **Review Enforcement Configuration**:
   - In GitHub Branch Protection / Repository Rulesets, setting *"Require approvals: 1"* would permanently block the sole owner from merging their own PRs (unless an independent authorized reviewer account exists).
   - Therefore, branch protection must strictly mandate:
     - **Require a pull request before merging** (blocks direct `git push` to `main`).
     - **Require status checks to pass before merging** (`verify-anchor-and-provenance`).
     - **Require linear history** (no merge commits; squash/rebase only).
     - **Do not allow bypass** (enforced on repository administrators).
   - When external or agent contributions are submitted via PR by other accounts, the Owner acts as the required approving reviewer.

---

## 2. Two-Stage Repository Bootstrap & Protection Roadmap

To prevent circular dependency locks during initial repository creation:

### Stage 1: Initial Protected Bootstrap (One-Time Setup)
1. **Initial Bootstrap Commit**:
   - An empty remote repository has no default branch to protect.
   - The initial foundation commit (15 audited files) is published to `main` via an **explicitly owner-authorized, one-time bootstrap push**.
2. **Immediate Protection Activation**:
   - Immediately following the initial push, the Owner activates GitHub Branch Protection / Ruleset on `main`:
     - Restrict direct pushes to `main` (all future changes require PR).
     - Require mandatory status check: `Verify Upstream Anchor Integrity` (job `verify-anchor-and-provenance`).
     - Enforce on administrators.
3. **Workflow Security Invariants**:
   - Default workflow permissions: `permissions: contents: read`.
   - All third-party GitHub Actions pinned to immutable 40-character commit SHAs.
   - Zero exposure of release or signing secrets in pull request workflows.

### Stage 2: Packaging Enforcement (Activated in Milestone P5)
Once packaging workflows (Windows, Ubuntu, macOS) are implemented and verified passing:
1. **Status Checks Expanded**:
   - `Verify Upstream Anchor Integrity`
   - `build-windows-package`
   - `build-ubuntu-package`
   - `build-macos-package`
   - `clean-machine-qualification`
2. **Protected Release Environment**:
   - Create GitHub Environment `Release-Publishing` with required manual reviewer (Repository Owner).
   - Code signing certificates and publishing tokens reside strictly inside `Release-Publishing` and are injected only on authorized release tags under explicit `OWNER PUBLISH GO`.

---

## 3. Core Technical Invariants

1. **Immutable Upstream Pinning**: Builds compile exclusively from the exact upstream commit SHA in `upstream_anchor.json`. The CI pipeline must never fetch floating branches (`main`, `master`, `HEAD`).
2. **Fail-Closed Execution**: Installers and native launchers enforce verifier-first admission. Corrupted bytecode, missing capabilities, or unverified SemCode cannot reach VM execution.
3. **Untrusted Code Isolation**: Launchers inspect OS security provenance (Windows Zone.Identifier, macOS `com.apple.quarantine`). Untrusted downloaded scripts require user confirmation.
4. **No Code Duplication**: Core compiler, semantic analysis, verifier, and VM code must never be duplicated or maintained in this repository.

---

## 4. Human Approval Gates (Explicit Owner Authority)

1. **`OWNER MERGE GO`**: Required before merging any PR into `main`.
2. **`OWNER PUBLISH GO`**: Required before tagging a release candidate (`v1.3.0-beta.1`) or uploading packages to GitHub Releases.
