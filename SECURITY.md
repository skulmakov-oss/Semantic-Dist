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

## 2. Four-Stage Repository Bootstrap & Protection Roadmap

To prevent circular dependency deadlocks during initial repository creation and the introduction of trusted admission:

### Stage 1: Initial Foundation Bootstrap (Completed in D0.3)
1. **Initial Bootstrap Commit**:
   - The initial foundation commit (15 audited files) was published to `main` via an **explicitly owner-authorized, one-time bootstrap push** (`d29e0609a1ecb76f611f2af06f7182ae58fd64e7`).
2. **Immediate Protection Activation**:
   - The Owner activated GitHub Ruleset on `main`:
     - Mandatory pull requests (no direct push).
     - Mandatory status check: `Verify Upstream Anchor Integrity` (context `Verify Upstream Anchor Integrity`, job `verify-anchor-and-provenance`).
     - Linear history and administrator enforcement.

### Stage 2: Introducing the Trusted Harness (Active D0.4 PR #1)
1. **Temporal Bootstrap Invariant**:
   - The trusted admission workflow (`.github/workflows/harness-trusted.yml`) runs on `pull_request_target` from the **base** branch (`main`).
   - While PR #1 is in-flight, `harness-trusted.yml` does not yet exist on `main`, so `pull_request_target` cannot execute from the base during PR #1's review.
   - Setting `Trusted PR Admission Check` as a required GitHub status check before PR #1 is merged would deadlock integration.
   - Therefore, PR #1 integration relies on:
     - Mandatory passing of `Verify Upstream Anchor Integrity` (which now runs Python 3.11 compilation and the complete adversarial admission test suite).
     - Independent security review.
     - Explicit **`OWNER MERGE GO`**.
2. **Feature Freeze During Transition**:
   - **No ordinary feature PR may be merged between D0.4 integration and Stage 3 enforcement.**

### Stage 3: Post-Merge Verification & Mandatory Status Check Cutover
Immediately following the merge of PR #1 into `main`:
1. The Owner verifies that `harness-trusted.yml` and `ci/trusted_pr_checker.py` exist on `main`.
2. A non-merging test PR is submitted under owner authorization to confirm that `Trusted PR Admission Check` (job `trusted-scope-admission`) executes and succeeds from the trusted base.
3. Once successful base-side execution is proven, the Owner updates the GitHub Branch Protection / Ruleset under separate **`OWNER PROTECTION GO`**:
   - Mandate **both** status checks before merge:
     1. `Verify Upstream Anchor Integrity` (untrusted PR payload verification)
     2. `Trusted PR Admission Check` (base-executed scope and control plane protection)
4. Verify via GitHub API that both checks are strictly required.
5. The temporary bootstrap exception is formally retired.

### Stage 4: Packaging & Release Environment Enforcement (Milestone P5)
Once packaging workflows (Windows, Ubuntu, macOS) are implemented under authorized governance:
1. **Status Checks Expanded**:
   - `Verify Upstream Anchor Integrity`
   - `Trusted PR Admission Check`
   - `build-windows-package`
   - `build-ubuntu-package`
   - `build-macos-package`
   - `clean-machine-qualification`
2. **Protected Release Environment**:
   - Create GitHub Environment `Release-Publishing` with required manual reviewer (Repository Owner).
   - Code signing certificates and publishing tokens reside strictly inside `Release-Publishing` and are injected only on authorized release tags under explicit `OWNER PUBLISH GO`.

---

## 3. Governance of Future CI Workflows (P2–P5 Workflow Maintainability)

The trusted checker enforces strict fail-closed protection over the control plane (`.github/workflows/**`, `ci/**`, `manifests/**`, `AGENTS.md`, `SECURITY.md`).

To ensure future legitimate packaging workflows (such as P2 launcher builds, P3 packaging matrices, and P5 signing) can be safely introduced without weakening trusted admission:

1. **Two-Phase Governance Transition Protocol**:
   - Ordinary feature PRs (`task.type: feature` or ordinary engineering PRs) cannot touch `.github/workflows/**` or protected control plane files. Any attempt fails admission immediately.
   - When a new CI workflow or workflow modification is required (e.g. adding `package-windows.yml`), it cannot be bundled into an ordinary feature PR.
   - It requires an **Owner-Authorized Governance Transition PR**:
     - The PR scope is strictly limited to the declared workflow addition/modification and corresponding governance documentation.
     - It must not include functional binary payloads or unvetted dependency updates.
     - It requires explicit, documented `OWNER GOVERNANCE GO` in the PR discussion thread before merge.
2. **Base-Side Invariant Immutability**:
   - `.github/workflows/harness-trusted.yml` and `ci/trusted_pr_checker.py` remain permanently protected. Even a governance transition PR is evaluated by the base revision of the trusted checker.
   - No bypass flag or secret override exists in the checker code.

---

## 4. Core Technical Invariants

1. **Immutable Upstream Pinning**: Builds compile exclusively from the exact upstream commit SHA in `upstream_anchor.json`. The CI pipeline must never fetch floating branches (`main`, `master`, `HEAD`).
2. **Fail-Closed Execution**: Installers and native launchers enforce verifier-first admission. Corrupted bytecode, missing capabilities, or unverified SemCode cannot reach VM execution.
3. **Untrusted Code Isolation**: Launchers inspect OS security provenance (Windows Zone.Identifier, macOS `com.apple.quarantine`). Untrusted downloaded scripts require user confirmation.
4. **No Code Duplication**: Core compiler, semantic analysis, verifier, and VM code must never be duplicated or maintained in this repository.

---

## 4. Human Approval Gates (Explicit Owner Authority)

1. **`OWNER MERGE GO`**: Required before merging any PR into `main`.
2. **`OWNER PUBLISH GO`**: Required before tagging a release candidate (`v1.3.0-beta.1`) or uploading packages to GitHub Releases.
