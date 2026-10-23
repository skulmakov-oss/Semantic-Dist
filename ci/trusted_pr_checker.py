#!/usr/bin/env python3
"""
Trusted PR Admission Checker for Semantic-Dist.

Executes in a trusted GitHub Actions environment (pull_request_target) on the base branch.
Inspects PR head commit as UNTRUSTED DATA only:
- Never executes candidate scripts or candidate workflows.
- Evaluates exact base/head commit SHAs.
- Detects attempts to modify protected verification workflows or checker scripts.
- Validates candidate anchor schema conformance as pure data.
- Ensures candidate does not modify the pinned upstream SHA without governance authorization.
"""

import sys
import os
import re
import json
import subprocess
import hashlib
from pathlib import Path

# Paths that are strictly protected from modification by ordinary PRs
PROTECTED_CONTROL_PLANE = {
    ".github/workflows/harness-trusted.yml",
    "ci/trusted_pr_checker.py",
}

# The pinned upstream commit SHA authorized by the repository owner
FROZEN_UPSTREAM_SHA = "1d1e76c7509a03baa0133abaaa5819f5d32582b2"

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

def check_admission(base_sha: str, head_sha: str, repo_root: Path):
    base_sha = validate_sha(base_sha, "base")
    head_sha = validate_sha(head_sha, "head")

    print(f"[trusted-checker] mode=trusted-pr base={base_sha} head={head_sha}")

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

    # 3. Guard against tampering with the trusted control plane
    for p in changed_paths:
        normalized_p = p.replace("\\", "/")
        if normalized_p in PROTECTED_CONTROL_PLANE:
            fail(f"unauthorized-control-plane-modification path={normalized_p}")

    # 4. If upstream_anchor.json is touched, validate candidate content as pure data
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

        # Check pinned upstream commit immutability
        candidate_sha = candidate_anchor.get("canonical_upstream", {}).get("pinned_commit_sha")
        if candidate_sha != FROZEN_UPSTREAM_SHA:
            fail(f"unauthorized-upstream-sha-transition candidate={candidate_sha} expected={FROZEN_UPSTREAM_SHA}")

        # Check SemCode policy validity
        policy = candidate_anchor.get("distribution_target", {}).get("semcode_policy", {})
        if policy.get("emission_default_header") != "SEMCOD22" or policy.get("emission_default_rev") != 23:
            fail(f"unsupported-semcode-emission-policy: {policy}")

    print("[trusted-checker] PASS mode=trusted-pr")

def main():
    if len(sys.argv) < 3:
        fail(f"Usage: {sys.argv[0]} <base_sha> <head_sha> [repo_root]")

    base_sha = sys.argv[1]
    head_sha = sys.argv[2]
    repo_root = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else Path(__file__).resolve().parent.parent

    check_admission(base_sha, head_sha, repo_root)

if __name__ == "__main__":
    main()
