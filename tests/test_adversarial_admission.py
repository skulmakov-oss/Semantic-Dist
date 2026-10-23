#!/usr/bin/env python3
"""
Adversarial Regression Test Suite for Semantic-Dist Provenance and Admission.

Covers:
1. Valid unchanged anchor -> PASS
2. Incorrect upstream commit SHA -> FAIL
3. Incorrect Cargo.lock SHA-256 -> FAIL
4. Incorrect Git blob OID -> FAIL
5. Anchor/schema mismatch -> FAIL
6. Unsupported or malformed SemCode policy -> FAIL
7. Unauthorized trusted workflow modification -> FAIL
8. Unauthorized checker modification -> FAIL
9. Candidate changes ordinary documentation only -> PASS
10. PR supplies unexpected executable content to checker -> safely treated as data / rejected
11. Incorrect base/head identity -> FAIL
"""

import sys
import os
import shutil
import json
import tempfile
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_DIR = REPO_ROOT / "ci"

class TestAdversarialAdmissionAndProvenance(unittest.TestCase):

    def run_cmd(self, cmd, cwd=None):
        res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode, res.stdout, res.stderr

    def create_fixture_base_and_candidate(self, tmp_dir: str):
        """Create a fixture repo where 'base' is an initial commit and candidate branches off it."""
        tmp_repo = Path(tmp_dir) / "repo"
        self.run_cmd(["git", "clone", str(REPO_ROOT), str(tmp_repo)])
        # Set author identity locally within the temporary test fixture repository
        self.run_cmd(["git", "config", "user.name", "Test Harness Runner"], cwd=tmp_repo)
        self.run_cmd(["git", "config", "user.email", "test-runner@semantic-dist.local"], cwd=tmp_repo)
        # In the clone, make a commit that represents the established base
        shutil.copytree(CI_DIR, tmp_repo / "ci", dirs_exist_ok=True)
        shutil.copytree(REPO_ROOT / ".github", tmp_repo / ".github", dirs_exist_ok=True)
        self.run_cmd(["git", "add", "."], cwd=tmp_repo)
        self.run_cmd(["git", "commit", "-qm", "established base with checker"], cwd=tmp_repo)
        ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
        base_sha = out.strip()
        return tmp_repo, base_sha

    def test_01_unchanged_authorized_upstream_anchor(self):
        """Test 1: Unchanged authorized upstream anchor passes verification."""
        ret, stdout, stderr = self.run_cmd([sys.executable, str(CI_DIR / "verify_provenance.py")], cwd=REPO_ROOT)
        self.assertEqual(ret, 0, f"Expected 0, got {ret}. Stderr: {stderr}")
        self.assertIn("[provenance] Upstream commit, Cargo.lock blob digest, and Git OID match: PASS", stdout)

    def test_02_incorrect_upstream_commit_sha(self):
        """Test 2: Candidate with incorrect upstream commit SHA fails trusted check."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            anchor_file = tmp_repo / "upstream_anchor.json"
            data = json.loads(anchor_file.read_text(encoding="utf-8"))
            data["canonical_upstream"]["pinned_commit_sha"] = "0000000000000000000000000000000000000000"
            anchor_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.run_cmd(["git", "add", "upstream_anchor.json"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "bad sha"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, bad_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertNotEqual(ret, 0)
            self.assertIn("unauthorized-upstream-sha-transition", stderr)

    def test_03_incorrect_cargo_lock_sha256(self):
        """Test 3: Incorrect Cargo.lock SHA-256 causes provenance verifier to fail."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, _ = self.create_fixture_base_and_candidate(tmp_dir)
            anchor_file = tmp_repo / "upstream_anchor.json"
            data = json.loads(anchor_file.read_text(encoding="utf-8"))
            data["canonical_upstream"]["cargo_lock_blob_sha256"] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
            anchor_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            ret, stdout, stderr = self.run_cmd([sys.executable, str(tmp_repo / "ci" / "verify_provenance.py")], cwd=tmp_repo)
            self.assertNotEqual(ret, 0)
            self.assertIn("Cargo.lock blob SHA-256 mismatch", stderr)

    def test_04_incorrect_git_blob_oid(self):
        """Test 4: Incorrect Git blob OID causes provenance verifier to fail."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, _ = self.create_fixture_base_and_candidate(tmp_dir)
            anchor_file = tmp_repo / "upstream_anchor.json"
            data = json.loads(anchor_file.read_text(encoding="utf-8"))
            data["canonical_upstream"]["cargo_lock_blob_git_oid"] = "0000000000000000000000000000000000000000"
            anchor_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            ret, stdout, stderr = self.run_cmd([sys.executable, str(tmp_repo / "ci" / "verify_provenance.py")], cwd=tmp_repo)
            self.assertNotEqual(ret, 0)
            self.assertIn("Cargo.lock Git OID mismatch", stderr)

    def test_05_anchor_schema_mismatch(self):
        """Test 5: Anchor missing required fields fails schema validation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, _ = self.create_fixture_base_and_candidate(tmp_dir)
            anchor_file = tmp_repo / "upstream_anchor.json"
            data = json.loads(anchor_file.read_text(encoding="utf-8"))
            del data["canonical_upstream"]["pinned_commit_sha"]
            anchor_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            ret, stdout, stderr = self.run_cmd([sys.executable, str(tmp_repo / "ci" / "verify_provenance.py")], cwd=tmp_repo)
            self.assertNotEqual(ret, 0)
            self.assertIn("Anchor schema validation failed", stderr)

    def test_06_unsupported_semcode_policy(self):
        """Test 6: Unsupported SemCode emission policy fails trusted check."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            anchor_file = tmp_repo / "upstream_anchor.json"
            data = json.loads(anchor_file.read_text(encoding="utf-8"))
            data["distribution_target"]["semcode_policy"]["emission_default_rev"] = 999
            anchor_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.run_cmd(["git", "add", "upstream_anchor.json"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "bad semcode policy"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, bad_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertNotEqual(ret, 0)
            self.assertIn("unsupported-semcode-emission-policy", stderr)

    def test_07_unauthorized_trusted_workflow_modification(self):
        """Test 7: Attempt to modify harness-trusted.yml fails closed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            wf_file = tmp_repo / ".github" / "workflows" / "harness-trusted.yml"
            wf_file.write_text("# malicious edit\n", encoding="utf-8")
            self.run_cmd(["git", "add", ".github/workflows/harness-trusted.yml"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch workflow"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, bad_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertNotEqual(ret, 0)
            self.assertIn("unauthorized-control-plane-modification path=.github/workflows/harness-trusted.yml", stderr)

    def test_08_unauthorized_checker_modification(self):
        """Test 8: Attempt to modify trusted_pr_checker.py fails closed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            checker_file = tmp_repo / "ci" / "trusted_pr_checker.py"
            checker_file.write_text("# malicious edit\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/trusted_pr_checker.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch checker"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, bad_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertNotEqual(ret, 0)
            self.assertIn("unauthorized-control-plane-modification path=ci/trusted_pr_checker.py", stderr)

    def test_08b_unauthorized_any_workflow_modification(self):
        """Test 8b: Attempt to modify verify-provenance.yml fails closed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            wf_file = tmp_repo / ".github" / "workflows" / "verify-provenance.yml"
            wf_file.write_text("# malicious workflow change\n", encoding="utf-8")
            self.run_cmd(["git", "add", ".github/workflows/verify-provenance.yml"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch other workflow"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, bad_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertNotEqual(ret, 0)
            self.assertIn("unauthorized-control-plane-modification path=.github/workflows/verify-provenance.yml", stderr)

    def test_08c_unauthorized_governance_file_modification(self):
        """Test 8c: Attempt to modify AGENTS.md or SECURITY.md fails closed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            sec_file = tmp_repo / "SECURITY.md"
            sec_file.write_text("# weakened security policy\n", encoding="utf-8")
            self.run_cmd(["git", "add", "SECURITY.md"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch SECURITY.md"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, bad_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertNotEqual(ret, 0)
            self.assertIn("unauthorized-control-plane-modification path=SECURITY.md", stderr)

    def test_08d_unauthorized_upstream_repo_transition(self):
        """Test 8d: Attempt to point upstream to an unauthorized repo fails closed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            anchor_file = tmp_repo / "upstream_anchor.json"
            data = json.loads(anchor_file.read_text(encoding="utf-8"))
            data["canonical_upstream"]["repository_url"] = "https://github.com/attacker-oss/Semantic"
            anchor_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.run_cmd(["git", "add", "upstream_anchor.json"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "point to attacker repo"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, bad_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertNotEqual(ret, 0)
            self.assertIn("unauthorized-upstream-repo-transition", stderr)

    def test_09_candidate_changes_ordinary_documentation_only(self):
        """Test 9: Candidate modifying only documentation passes trusted admission."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            doc_file = tmp_repo / "docs" / "architecture.md"
            doc_file.write_text(doc_file.read_text(encoding="utf-8") + "\n<!-- ordinary edit -->\n", encoding="utf-8")
            self.run_cmd(["git", "add", "docs/architecture.md"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "docs edit"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            good_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, good_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertEqual(ret, 0, f"Expected 0, got {ret}. Stderr: {stderr}")
            self.assertIn("[trusted-checker] PASS mode=trusted-pr", stdout)

    def test_10_candidate_supplies_executable_script_content(self):
        """Test 10: Candidate supplying shell scripts or binaries is treated as pure untrusted data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            exploit_file = tmp_repo / "exploit.sh"
            exploit_file.write_text("#!/bin/bash\necho PWNED > /tmp/pwn\n", encoding="utf-8")
            self.run_cmd(["git", "add", "exploit.sh"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add exploit"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            exploit_head_sha = out.strip()

            ret, stdout, stderr = self.run_cmd(
                [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), base_sha, exploit_head_sha, str(tmp_repo)],
                cwd=REPO_ROOT
            )
            self.assertEqual(ret, 0, f"Expected 0, got {ret}. Stderr: {stderr}")
            self.assertIn("[trusted-checker:path] exploit.sh", stdout)
            self.assertIn("[trusted-checker] PASS mode=trusted-pr", stdout)

    def test_11_incorrect_base_or_head_identity(self):
        """Test 11: Non-existent base or head SHA fails immediately."""
        ret, stdout, stderr = self.run_cmd(
            [sys.executable, str(CI_DIR / "trusted_pr_checker.py"), "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "1234567890123456789012345678901234567890", str(REPO_ROOT)],
            cwd=REPO_ROOT
        )
        self.assertNotEqual(ret, 0)
        self.assertIn("is not a valid commit object", stderr)

if __name__ == "__main__":
    unittest.main()
