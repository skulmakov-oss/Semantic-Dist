#!/usr/bin/env python3
"""
Trusted PR Admission Checker for Semantic-Dist.

Executes in a trusted GitHub Actions environment (pull_request_target) on the base branch.
Inspects PR head commit as UNTRUSTED DATA only:
- Never executes candidate scripts or candidate workflows.
- Evaluates exact base/head commit SHAs.
- Distinguishes ordinary PRs from owner-authorized governance transition PRs.
- Ordinary PRs: strictly prohibited from modifying control plane paths.
- Governance PRs: require independently verifiable OWNER GOVERNANCE GO from authenticated GitHub API.
- Validates candidate anchor and governance schema conformance as pure data.
"""

import sys
import os
import re
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

TRUSTED_REPO_OWNER = "skulmakov-oss"
TRUSTED_REPO_NAME = "Semantic-Dist"
TRUSTED_REPOSITORY = f"{TRUSTED_REPO_OWNER}/{TRUSTED_REPO_NAME}"

PROTECTED_CONTROL_PLANE_EXACT = {
    "AGENTS.md",
    "SECURITY.md",
    "upstream_anchor.json",
}

PROTECTED_CONTROL_PLANE_PREFIXES = (
    ".github/",
    "ci/",
    "manifests/",
)

FROZEN_UPSTREAM = {
    "repository_url": "https://github.com/skulmakov-oss/Semantic",
    "pinned_commit_sha": "1d1e76c7509a03baa0133abaaa5819f5d32582b2",
    "cargo_lock_blob_sha256": "5d85791ca1194f6fc6142ed96b1d3bf5ca0f4b05104689f824f364f7a4e6c0d8",
    "cargo_lock_blob_git_oid": "6111b565dd0c71383e3f184ebdec23c4a502f58c",
    "rust_toolchain_channel": "1.97.1",
}

def fail(msg: str, code: int = 1):
    print(f"[trusted-checker:error] {msg}", file=sys.stderr)
    sys.exit(code)

def run_git(args: list[str], repo_root: Path) -> tuple[int, bytes, bytes]:
    res = subprocess.run(["git", "-C", str(repo_root)] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode, res.stdout, res.stderr

def validate_sha(sha: str, label: str) -> str:
    if not re.match(r"^[0-9a-fA-F]{40}$", sha):
        fail(f"Invalid {label} SHA format: {sha}")
    return sha.lower()

def is_protected_control_plane(path_str: str) -> bool:
    normalized = path_str.replace("\\", "/").lstrip("/")
    if normalized in PROTECTED_CONTROL_PLANE_EXACT:
        return True
    for prefix in PROTECTED_CONTROL_PLANE_PREFIXES:
        if normalized.startswith(prefix):
            return True
    return False

def fetch_github_comments(repo: str, pr_number: int, github_token: str | None) -> list[dict]:
    comments: list[dict] = []
    next_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments?per_page=100"
    pages_fetched = 0
    max_pages = 50  # fail-safe upper bound against runaway pagination

    while next_url and pages_fetched < max_pages:
        req = urllib.request.Request(next_url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "Semantic-Dist-Trusted-Checker")
        if github_token:
            req.add_header("Authorization", f"Bearer {github_token}")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    fail(f"GitHub API returned HTTP {resp.status} fetching comments for PR #{pr_number}")
                data = json.loads(resp.read().decode("utf-8"))
                if not isinstance(data, list):
                    fail(f"Malformed comments payload received from GitHub API for PR #{pr_number}")
                comments.extend(data)

                # Parse pagination from Link header
                link_header = resp.headers.get("Link", "")
                next_url = None
                if link_header:
                    links = link_header.split(",")
                    for link in links:
                        parts = link.split(";")
                        if len(parts) >= 2:
                            url_part = parts[0].strip()
                            rel_part = parts[1].strip()
                            if rel_part == 'rel="next"' and url_part.startswith("<") and url_part.endswith(">"):
                                next_url = url_part[1:-1]
                                break
        except Exception as e:
            fail(f"Failed to query GitHub API for PR #{pr_number} comments: {e}")
        pages_fetched += 1

    return comments

def parse_and_verify_governance_authorization(
    comments: list[dict],
    expected_repo: str,
    expected_pr: int,
    expected_base: str,
    expected_head: str,
    changed_control_plane: list[str],
) -> dict:
    """
    Search comments for authenticated owner authorization matching exact PR, BASE, HEAD, and path scope.
    Pattern:
    ```governance-authorization
    {
      "version": "1.0.0",
      "repository": "skulmakov-oss/Semantic-Dist",
      "pr_number": 1,
      "base_sha": "...",
      "head_sha": "...",
      "decision": "OWNER GOVERNANCE GO",
      "authorized_paths": [ ... ]
    }
    ```
    """
    valid_authorizations = []
    has_revocation = False

    for comment in comments:
        user = comment.get("user", {})
        login = user.get("login")
        author_association = comment.get("author_association")
        body = comment.get("body", "")

        # Check for explicit revocation by owner
        if login == TRUSTED_REPO_OWNER or author_association == "OWNER":
            if f"REVOKE GOVERNANCE GO {expected_head}" in body or f"REVOKE GOVERNANCE GO PR#{expected_pr}" in body:
                has_revocation = True

            # Match JSON authorization blocks
            pattern = r"```governance-authorization\s*([\s\S]*?)\s*```"
            matches = re.findall(pattern, body)
            for m in matches:
                try:
                    auth_data = json.loads(m.strip())
                except Exception:
                    continue

                if auth_data.get("decision") != "OWNER GOVERNANCE GO":
                    continue
                if auth_data.get("repository") != expected_repo:
                    continue
                if auth_data.get("pr_number") != expected_pr:
                    continue
                if auth_data.get("base_sha", "").lower() != expected_base.lower():
                    continue
                if auth_data.get("head_sha", "").lower() != expected_head.lower():
                    continue

                valid_authorizations.append(auth_data)

    if has_revocation:
        fail(f"unauthorized-governance: explicit revocation found for HEAD {expected_head}")

    if not valid_authorizations:
        fail(f"unauthorized-governance: no valid authenticated OWNER GOVERNANCE GO for PR #{expected_pr} HEAD {expected_head}")

    # Use the latest valid authorization
    latest_auth = valid_authorizations[-1]
    authorized_paths_set = set(p.replace("\\", "/").lstrip("/") for p in latest_auth.get("authorized_paths", []))

    # Verify every touched control plane path is explicitly authorized
    for p in changed_control_plane:
        normalized_p = p.replace("\\", "/").lstrip("/")
        if normalized_p not in authorized_paths_set:
            fail(f"unauthorized-governance-path-scope path={normalized_p} not in authorized_paths")

    print(f"[trusted-checker:governance] authenticated OWNER GOVERNANCE GO verified for PR #{expected_pr} HEAD {expected_head}")
    return latest_auth

def check_admission(base_sha: str, head_sha: str, repo_root: Path, pr_number: int | None = None, mock_comments: list[dict] | None = None):
    base_sha = validate_sha(base_sha, "base")
    head_sha = validate_sha(head_sha, "head")

    print(f"[trusted-checker] mode=trusted-pr base={base_sha} head={head_sha} pr={pr_number}")

    # 1. Verify commit objects exist
    ret, out, _ = run_git(["cat-file", "-t", base_sha], repo_root)
    if ret != 0 or out.strip() != b"commit":
        fail(f"Base ref {base_sha} is not a valid commit object")

    ret, out, _ = run_git(["cat-file", "-t", head_sha], repo_root)
    if ret != 0 or out.strip() != b"commit":
        fail(f"Head ref {head_sha} is not a valid commit object")

    # 2. Extract paths touched between base and head
    ret, out, err = run_git(["diff", "--name-only", "-z", "--no-renames", base_sha, head_sha, "--"], repo_root)
    if ret != 0:
        fail(f"Failed to inspect git diff between {base_sha} and {head_sha}: {err.decode(errors='replace')}")

    raw_paths = out.split(b"\0")
    changed_paths = [p.decode(errors="replace") for p in raw_paths if p]
    changed_paths.sort()

    for p in changed_paths:
        print(f"[trusted-checker:path] {p}")

    # 3. Classify control-plane paths
    control_plane_changed = [p for p in changed_paths if is_protected_control_plane(p)]

    # 4. If control-plane paths are touched, require verified OWNER GOVERNANCE GO
    if control_plane_changed:
        print(f"[trusted-checker:mode] governance-transition control_plane_paths={len(control_plane_changed)}")
        if pr_number is None or pr_number <= 0:
            fail(f"unauthorized-control-plane-modification: governance changes require a valid pull request number")

        # Fetch authenticated comments from GitHub API or use test fixture mock
        if mock_comments is not None:
            comments = mock_comments
        else:
            token = os.environ.get("GITHUB_TOKEN")
            repo_env = os.environ.get("GITHUB_REPOSITORY", TRUSTED_REPOSITORY)
            comments = fetch_github_comments(repo_env, pr_number, token)

        # Validate owner authorization
        repo_target = os.environ.get("GITHUB_REPOSITORY", TRUSTED_REPOSITORY)
        parse_and_verify_governance_authorization(
            comments,
            repo_target,
            pr_number,
            base_sha,
            head_sha,
            control_plane_changed
        )

    # 5. If upstream_anchor.json is touched, validate candidate content as pure data
    if "upstream_anchor.json" in changed_paths:
        ret, candidate_anchor_bytes, err = run_git(["cat-file", "-p", f"{head_sha}:upstream_anchor.json"], repo_root)
        if ret != 0:
            fail(f"Failed to read candidate upstream_anchor.json from {head_sha}")

        try:
            candidate_anchor = json.loads(candidate_anchor_bytes.decode("utf-8"))
        except Exception as e:
            fail(f"Candidate upstream_anchor.json is malformed JSON: {e}")

        # Read base anchor schema as authoritative
        schema_path = repo_root / "manifests" / "anchor_schema.json"
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as e:
            fail(f"Authoritative anchor_schema.json cannot be read: {e}")

        try:
            import jsonschema
            jsonschema.Draft202012Validator.check_schema(schema)
            validator = jsonschema.Draft202012Validator(schema)
            validator.validate(candidate_anchor)
        except Exception as e:
            fail(f"Candidate upstream_anchor.json fails schema validation: {e}")

        # For ordinary PRs (or unexempted transitions), check immutable canonical upstream invariants
        if not control_plane_changed:
            upstream = candidate_anchor.get("canonical_upstream", {})
            if upstream.get("repository_url") != FROZEN_UPSTREAM["repository_url"]:
                fail(f"unauthorized-upstream-repo-transition candidate={upstream.get('repository_url')} expected={FROZEN_UPSTREAM['repository_url']}")

            candidate_sha = upstream.get("pinned_commit_sha")
            if candidate_sha != FROZEN_UPSTREAM["pinned_commit_sha"]:
                fail(f"unauthorized-upstream-sha-transition candidate={candidate_sha} expected={FROZEN_UPSTREAM['pinned_commit_sha']}")

            if upstream.get("cargo_lock_blob_sha256") != FROZEN_UPSTREAM["cargo_lock_blob_sha256"]:
                fail(f"unauthorized-cargo-lock-sha256-transition candidate={upstream.get('cargo_lock_blob_sha256')} expected={FROZEN_UPSTREAM['cargo_lock_blob_sha256']}")

            if upstream.get("cargo_lock_blob_git_oid") != FROZEN_UPSTREAM["cargo_lock_blob_git_oid"]:
                fail(f"unauthorized-cargo-lock-oid-transition candidate={upstream.get('cargo_lock_blob_git_oid')} expected={FROZEN_UPSTREAM['cargo_lock_blob_git_oid']}")

            toolchain_channel = upstream.get("rust_toolchain", {}).get("channel")
            if toolchain_channel != FROZEN_UPSTREAM["rust_toolchain_channel"]:
                fail(f"unauthorized-toolchain-channel-transition candidate={toolchain_channel} expected={FROZEN_UPSTREAM['rust_toolchain_channel']}")

        # Check SemCode policy validity
        policy = candidate_anchor.get("distribution_target", {}).get("semcode_policy", {})
        if policy.get("emission_default_header") != "SEMCOD22" or policy.get("emission_default_rev") != 23:
            fail(f"unsupported-semcode-emission-policy: {policy}")

    print("[trusted-checker] PASS mode=trusted-pr")

def main():
    if len(sys.argv) < 3:
        fail(f"Usage: {sys.argv[0]} <base_sha> <head_sha> [repo_root] [pr_number]")

    base_sha = sys.argv[1]
    head_sha = sys.argv[2]
    repo_root = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 and sys.argv[3] else Path(__file__).resolve().parent.parent
    pr_number_raw = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("PR_NUMBER")
    pr_number = int(pr_number_raw) if pr_number_raw and pr_number_raw.isdigit() else None

    check_admission(base_sha, head_sha, repo_root, pr_number=pr_number)

if __name__ == "__main__":
    main()
