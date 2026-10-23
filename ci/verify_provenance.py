#!/usr/bin/env python3
"""
Verify Canonical Upstream Provenance for Semantic-Dist.

Reads manifests/anchor_schema.json and upstream_anchor.json.
Validates anchor against schema.
Fetches canonical upstream repository at the exact pinned SHA.
Asserts byte-for-byte identity of the raw Cargo.lock Git blob and Git object OID.
"""

import sys
import os
import json
import subprocess
import hashlib
from pathlib import Path

def fail(msg: str, code: int = 1):
    print(f"[provenance:error] {msg}", file=sys.stderr)
    sys.exit(code)

def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, bytes, bytes]:
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode, res.stdout, res.stderr

def main():
    root = Path(__file__).resolve().parent.parent
    anchor_path = root / "upstream_anchor.json"
    schema_path = root / "manifests" / "anchor_schema.json"

    if not anchor_path.is_file():
        fail(f"Missing upstream_anchor.json at {anchor_path}")
    if not schema_path.is_file():
        fail(f"Missing anchor_schema.json at {schema_path}")

    # 1. Parse JSON
    try:
        with open(anchor_path, "r", encoding="utf-8") as f:
            anchor = json.load(f)
    except Exception as e:
        fail(f"Invalid JSON in {anchor_path}: {e}")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        fail(f"Invalid JSON in {schema_path}: {e}")

    # 2. Schema Validation
    try:
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(schema)
        validator = jsonschema.Draft202012Validator(schema)
        validator.validate(anchor)
    except Exception as e:
        fail(f"Anchor schema validation failed: {e}")

    print("[provenance] Anchor schema validation: PASS")

    # 3. Extract dynamically from validated anchor
    canonical = anchor.get("canonical_upstream", {})
    repo_url = canonical.get("repository_url")
    pinned_sha = canonical.get("pinned_commit_sha")
    expected_blob_sha256 = canonical.get("cargo_lock_blob_sha256")
    expected_git_oid = canonical.get("cargo_lock_blob_git_oid")

    if not repo_url or not pinned_sha or not expected_blob_sha256 or not expected_git_oid:
        fail("Anchor missing required upstream identity fields")

    print(f"[provenance] Upstream Repository: {repo_url}")
    print(f"[provenance] Pinned SHA: {pinned_sha}")
    print(f"[provenance] Expected Cargo.lock blob SHA-256: {expected_blob_sha256}")
    print(f"[provenance] Expected Cargo.lock Git OID: {expected_git_oid}")

    # 4. Clone / checkout upstream in temporary directory
    target_dir = root / ".upstream_cache"
    if not (target_dir / ".git").is_dir():
        target_dir.mkdir(parents=True, exist_ok=True)
        ret, out, err = run_cmd(["git", "clone", "--no-checkout", repo_url, str(target_dir)])
        if ret != 0:
            fail(f"Failed to clone upstream repository {repo_url}: {err.decode(errors='replace')}")

    # Fetch exact pinned SHA
    ret, out, err = run_cmd(["git", "fetch", "--depth", "1", "origin", pinned_sha], cwd=target_dir)
    if ret != 0:
        # Fallback to full fetch if shallow fetch by commit fails
        ret, out, err = run_cmd(["git", "fetch", "origin"], cwd=target_dir)
        if ret != 0:
            fail(f"Failed to fetch upstream commit {pinned_sha}: {err.decode(errors='replace')}")

    # Verify commit exists and is a valid commit object
    ret, out, err = run_cmd(["git", "cat-file", "-t", pinned_sha], cwd=target_dir)
    if ret != 0 or out.strip() != b"commit":
        fail(f"Upstream SHA {pinned_sha} is not a valid commit in {repo_url}")

    # 5. Extract raw Cargo.lock Git blob bytes without checkout / CRLF transformation
    ret, out, err = run_cmd(["git", "rev-parse", f"{pinned_sha}:Cargo.lock"], cwd=target_dir)
    if ret != 0:
        fail(f"Failed to find Cargo.lock at upstream commit {pinned_sha}: {err.decode(errors='replace')}")
    actual_git_oid = out.strip().decode()

    ret, raw_blob, err = run_cmd(["git", "cat-file", "-p", f"{pinned_sha}:Cargo.lock"], cwd=target_dir)
    if ret != 0:
        fail(f"Failed to read Cargo.lock blob from {pinned_sha}: {err.decode(errors='replace')}")

    actual_blob_sha256 = hashlib.sha256(raw_blob).hexdigest().lower()

    # 6. Cryptographic Comparison
    print(f"[provenance] Actual Cargo.lock Git OID: {actual_git_oid}")
    print(f"[provenance] Actual Cargo.lock blob SHA-256: {actual_blob_sha256}")

    if actual_git_oid.lower() != expected_git_oid.lower():
        fail(f"Cargo.lock Git OID mismatch! Expected {expected_git_oid}, got {actual_git_oid}")

    if actual_blob_sha256 != expected_blob_sha256.lower():
        fail(f"Cargo.lock blob SHA-256 mismatch! Expected {expected_blob_sha256}, got {actual_blob_sha256}")

    print("[provenance] Upstream commit, Cargo.lock blob digest, and Git OID match: PASS")

if __name__ == "__main__":
    main()
