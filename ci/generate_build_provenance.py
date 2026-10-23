#!/usr/bin/env python3
"""
Generate build provenance metadata for Semantic-Dist Windows installer.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def main():
    root = Path(__file__).resolve().parent.parent
    dist_dir = root / "packaging" / "windows" / "dist"
    staging_dir = root / "dist-staging" / "bin"
    output_path = root / "build_provenance.json"

    installer = dist_dir / "Semantic-Setup-x64.exe"
    smc = staging_dir / "smc.exe"
    svm = staging_dir / "svm.exe"
    sm_launch = staging_dir / "sm-launch.exe"

    for p in [installer, smc, svm, sm_launch]:
        if not p.is_file():
            print(f"[error] Artifact file not found: {p}", file=sys.stderr)
            sys.exit(1)

    anchor_path = root / "upstream_anchor.json"
    with open(anchor_path, "r", encoding="utf-8") as f:
        anchor = json.load(f)

    canonical = anchor.get("canonical_upstream", {})

    # Capture environment or git info
    source_sha = os.environ.get("GITHUB_SHA", "local")
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")

    provenance = {
        "product_name": "Semantic",
        "product_version": "1.3.0-beta.1",
        "release_channel": "developer-preview",
        "classification": "Unsigned Developer Preview — Not a Published Release",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflow_run_identity": {
            "github_run_id": run_id,
            "github_run_attempt": run_attempt,
            "commit_sha": source_sha
        },
        "upstream": {
            "repository_url": canonical.get("repository_url"),
            "pinned_commit_sha": canonical.get("pinned_commit_sha"),
            "cargo_lock_blob_sha256": canonical.get("cargo_lock_blob_sha256"),
            "cargo_lock_blob_git_oid": canonical.get("cargo_lock_blob_git_oid")
        },
        "build_environment": {
            "rustc_version": "1.97.1",
            "target_triple": "x86_64-pc-windows-msvc",
            "inno_setup_version": "6.7.x"
        },
        "artifacts": {
            "installer": {
                "filename": "Semantic-Setup-x64.exe",
                "sha256": compute_sha256(installer),
                "bytes": installer.stat().st_size
            },
            "binaries": {
                "smc.exe": {
                    "sha256": compute_sha256(smc),
                    "bytes": smc.stat().st_size
                },
                "svm.exe": {
                    "sha256": compute_sha256(svm),
                    "bytes": svm.stat().st_size
                },
                "sm-launch.exe": {
                    "sha256": compute_sha256(sm_launch),
                    "bytes": sm_launch.stat().st_size
                }
            }
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2)

    print(f"[provenance] Generated build provenance at {output_path}")

if __name__ == "__main__":
    main()
