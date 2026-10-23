#!/usr/bin/env python3
"""
Provenance Regression Test Suite for Semantic-Dist.

Focuses exclusively on canonical upstream provenance invariants:
1. Valid canonical upstream identity -> PASS
2. Incorrect upstream commit SHA -> FAIL
3. Incorrect Cargo.lock SHA-256 -> FAIL
4. Incorrect Git blob OID -> FAIL
5. Invalid or incomplete anchor JSON -> FAIL
6. Invalid anchor schema -> FAIL
"""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_DIR = REPO_ROOT / "ci"
ANCHOR_FILE = REPO_ROOT / "upstream_anchor.json"
SCHEMA_FILE = REPO_ROOT / "manifests" / "anchor_schema.json"
VERIFIER_SCRIPT = CI_DIR / "verify_provenance.py"

import jsonschema


class TestProvenanceValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ANCHOR_FILE, "r", encoding="utf-8") as f:
            cls.valid_anchor = json.load(f)
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            cls.valid_schema = json.load(f)

    def test_01_canonical_upstream_identity_passes_schema(self):
        """Valid canonical upstream anchor must pass schema validation."""
        jsonschema.Draft202012Validator.check_schema(self.valid_schema)
        validator = jsonschema.Draft202012Validator(self.valid_schema)
        validator.validate(self.valid_anchor)

    def test_02_incorrect_upstream_sha_fails(self):
        """Tampered upstream commit SHA must fail schema pattern or verifier assertion."""
        tampered = copy.deepcopy(self.valid_anchor)
        tampered["canonical_upstream"]["pinned_commit_sha"] = "0000000000000000000000000000000000000000"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "manifests").mkdir()
            (tmp_root / "ci").mkdir()
            with open(tmp_root / "upstream_anchor.json", "w", encoding="utf-8") as f:
                json.dump(tampered, f)
            with open(tmp_root / "manifests" / "anchor_schema.json", "w", encoding="utf-8") as f:
                json.dump(self.valid_schema, f)
            shutil_script = tmp_root / "ci" / "verify_provenance.py"
            shutil_script.write_text(VERIFIER_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")

            # Run verifier script against tampered anchor
            res = subprocess.run([sys.executable, str(shutil_script)], cwd=tmp_root, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("[provenance:error]", res.stderr)

    def test_03_incorrect_cargo_lock_sha256_fails(self):
        """Tampered Cargo.lock SHA-256 digest must fail verification."""
        tampered = copy.deepcopy(self.valid_anchor)
        tampered["canonical_upstream"]["cargo_lock_blob_sha256"] = "a" * 64

        validator = jsonschema.Draft202012Validator(self.valid_schema)
        validator.validate(tampered)  # passes regex pattern

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "manifests").mkdir()
            (tmp_root / "ci").mkdir()
            # Reuse cached clone if available to avoid unnecessary network
            cache_src = REPO_ROOT / ".upstream_cache"
            if cache_src.is_dir():
                import shutil
                shutil.copytree(cache_src, tmp_root / ".upstream_cache")

            with open(tmp_root / "upstream_anchor.json", "w", encoding="utf-8") as f:
                json.dump(tampered, f)
            with open(tmp_root / "manifests" / "anchor_schema.json", "w", encoding="utf-8") as f:
                json.dump(self.valid_schema, f)
            shutil_script = tmp_root / "ci" / "verify_provenance.py"
            shutil_script.write_text(VERIFIER_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")

            res = subprocess.run([sys.executable, str(shutil_script)], cwd=tmp_root, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("Cargo.lock blob SHA-256 mismatch", res.stderr)

    def test_04_incorrect_git_oid_fails(self):
        """Tampered Git blob OID must fail verification."""
        tampered = copy.deepcopy(self.valid_anchor)
        tampered["canonical_upstream"]["cargo_lock_blob_git_oid"] = "b" * 40

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "manifests").mkdir()
            (tmp_root / "ci").mkdir()
            cache_src = REPO_ROOT / ".upstream_cache"
            if cache_src.is_dir():
                import shutil
                shutil.copytree(cache_src, tmp_root / ".upstream_cache")

            with open(tmp_root / "upstream_anchor.json", "w", encoding="utf-8") as f:
                json.dump(tampered, f)
            with open(tmp_root / "manifests" / "anchor_schema.json", "w", encoding="utf-8") as f:
                json.dump(self.valid_schema, f)
            shutil_script = tmp_root / "ci" / "verify_provenance.py"
            shutil_script.write_text(VERIFIER_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")

            res = subprocess.run([sys.executable, str(shutil_script)], cwd=tmp_root, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("Cargo.lock Git OID mismatch", res.stderr)

    def test_05_invalid_or_incomplete_anchor_json_fails(self):
        """Missing required fields in anchor JSON must be rejected by schema validator."""
        incomplete_anchor = copy.deepcopy(self.valid_anchor)
        del incomplete_anchor["canonical_upstream"]["pinned_commit_sha"]

        validator = jsonschema.Draft202012Validator(self.valid_schema)
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(incomplete_anchor)

        malformed_sha_anchor = copy.deepcopy(self.valid_anchor)
        malformed_sha_anchor["canonical_upstream"]["pinned_commit_sha"] = "not-a-40-hex-sha"
        with self.assertRaises(jsonschema.ValidationError):
            validator.validate(malformed_sha_anchor)

    def test_06_invalid_anchor_schema_fails(self):
        """An invalid schema definition must fail Draft202012 schema check."""
        invalid_schema = copy.deepcopy(self.valid_schema)
        invalid_schema["type"] = "unsupported_type"

        with self.assertRaises(jsonschema.SchemaError):
            jsonschema.Draft202012Validator.check_schema(invalid_schema)


if __name__ == "__main__":
    unittest.main()
