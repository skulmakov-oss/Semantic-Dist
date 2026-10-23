# Security & Governance Policy — Semantic-Dist

Status: Normative Repository Governance Authority  
Applies to: `skulmakov-oss/Semantic-Dist`

---

## 1. Governance Model for Sole-Owner Repository

In GitHub, a pull request author **cannot approve their own pull request**. In a single-maintainer repository where the repository owner authors PRs or directs agent contributions:

1. **Owner Authority**:
   - Explicit owner authorization is documented directly in the issue/PR discussion thread as a formal governance record (`OWNER GOVERNANCE GO`, `OWNER MERGE GO`, `OWNER PUBLISH GO`, `OWNER PROTECTION GO`).
2. **Review Enforcement Configuration**:
   - In GitHub Branch Protection / Repository Rulesets, setting *"Require approvals: 1"* would permanently block the sole owner from merging their own PRs (unless an independent authorized reviewer account exists).
   - Therefore, branch protection strictly mandates:
     - **Require a pull request before merging** (blocks direct `git push` to `main`).
     - **Require status checks to pass before merging** (`Verify Upstream Anchor Integrity` and, post-cutover, `Trusted PR Admission Check`).
     - **Require linear history** (no merge commits; squash/rebase only).
     - **Do not allow bypass** (enforced on repository administrators).
   - When external or agent contributions are submitted via PR by other accounts, the Owner acts as the required approving reviewer.

---

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
     - Mandatory passing of `Verify Upstream Anchor Integrity` (which executes Python 3.11 compilation and the complete adversarial admission test suite).
     - Independent security review.
     - Explicit **`OWNER MERGE GO`**.
2. **Feature Freeze During Transition**:
   - **No ordinary feature PR may be merged between D0.4 integration and Stage 3 enforcement.**

### Stage 3: Post-Merge Verification & Mandatory Status Check Cutover
Immediately following the merge of PR #1 into `main`:
1. The Owner verifies that `harness-trusted.yml` and `ci/trusted_pr_checker.py` exist on `main`.
2. A non-merging test PR is submitted under owner authorization to confirm that `Trusted PR Admission Check` (job `trusted-scope-admission`) executes and succeeds from the trusted base.
3. An adversarial probe PR attempting to touch protected paths without owner authorization confirms immediate base-side fail-closed rejection.
4. Once successful base-side execution is proven, the Owner updates the GitHub Branch Protection / Ruleset under separate **`OWNER PROTECTION GO`**:
   - Mandate **both** status checks before merge:
     1. `Verify Upstream Anchor Integrity` (untrusted PR payload verification)
     2. `Trusted PR Admission Check` (base-executed scope and control plane protection)
5. Verify via GitHub API that both checks are strictly required.
6. The temporary bootstrap exception is formally retired.

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

## 3. Governance Admission & Control Plane Protection (P2–P5 Workflow Maintainability)

The trusted checker enforces strict fail-closed protection over the control plane:
- **Protected Prefixes**: `.github/`, `ci/`, `manifests/`
- **Protected Exact Paths**: `AGENTS.md`, `SECURITY.md`, `upstream_anchor.json`

### PR Surface Classification:
1. **Ordinary PRs**:
   - Permitted only on ordinary engineering paths (`launcher/**`, `packaging/**`, `docs/**`, `tests/**`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, etc.).
   - May never add, remove, rename, or modify any file in the protected control plane. Any ordinary PR touching control plane paths fails admission immediately.
2. **Governance Transition PRs**:
   - Permitted when adding or modifying packaging workflows (P2–P5), updating CI tools, or amending governance contracts.
   - Requires an authenticated **`OWNER GOVERNANCE GO`** recorded as an official comment on the PR by the repository owner (`skulmakov-oss`).
   - The authorization must be structured, binding exact repository, PR number, BASE SHA, HEAD SHA, and explicit authorized paths:
     ```governance-authorization
     {
       "version": "1.0.0",
       "decision": "OWNER GOVERNANCE GO",
       "repository": "skulmakov-oss/Semantic-Dist",
       "pr_number": 1,
       "base_sha": "<BASE_SHA>",
       "head_sha": "<HEAD_SHA>",
       "authorized_paths": [
         ".github/workflows/package-windows.yml"
       ]
     }
     ```
   - Candidate-controlled claims (in commit messages, PR descriptions, labels, or candidate YAML files) have **zero authority**. Authorization is retrieved and verified strictly via authenticated GitHub API calls by the trusted base checker.
   - Any new commit pushed to the PR invalidates earlier authorization, requiring fresh owner review.
   - An explicit owner revocation (`REVOKE GOVERNANCE GO <HEAD_SHA>`) fails admission immediately.

---

## 4. Core Technical Invariants

1. **Immutable Upstream Pinning**: Builds compile exclusively from the exact upstream commit SHA in `upstream_anchor.json`. The CI pipeline must never fetch floating branches (`main`, `master`, `HEAD`).
2. **Fail-Closed Execution**: Installers and native launchers enforce verifier-first admission. Corrupted bytecode, missing capabilities, or unverified SemCode cannot reach VM execution.
3. **Untrusted Code Isolation**: Launchers inspect OS security provenance (Windows Zone.Identifier, macOS `com.apple.quarantine`). Untrusted downloaded scripts require user confirmation.
4. **No Code Duplication**: Core compiler, semantic analysis, verifier, and VM code must never be duplicated or maintained in this repository.
5. **Immutable Base Execution**: Pull request evaluation runs base-branch verification code only; untrusted candidate objects are inspected as pure inert data.

---

## 5. Human Approval Gates (Explicit Owner Authority)

1. **`OWNER GOVERNANCE GO`**: Required to authorize a governance transition PR touching control plane paths.
2. **`OWNER MERGE GO`**: Required before merging any PR into `main`.
3. **`OWNER PROTECTION GO`**: Required before modifying repository rulesets or branch protection.
4. **`OWNER PUBLISH GO`**: Required before tagging a release candidate (`v1.3.0-beta.1`) or uploading packages to GitHub Releases.
