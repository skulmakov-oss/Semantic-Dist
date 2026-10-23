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
8b. Unauthorized .github/actions modification -> FAIL
8c. Unauthorized new ci/package.py modification -> FAIL
8d. Unauthorized new manifests/new_schema.json modification -> FAIL
8e. Unauthorized SECURITY.md modification -> FAIL
8f. Fake owner approval in PR description -> FAIL
8g. Fake owner approval in candidate YAML -> FAIL
8h. Approval from a non-owner -> FAIL
8i. Approval for an earlier HEAD SHA -> FAIL
8j. Approval for a different PR number -> FAIL
8k. Approval with insufficient path scope -> FAIL
8l. GitHub API error / malformed response -> FAIL
8m. Explicit owner revocation -> FAIL
9. Candidate changes ordinary documentation only -> PASS
9b. Candidate changes ordinary launcher source only -> PASS
10. PR supplies unexpected executable content to checker -> safely treated as data / rejected
11. Incorrect base/head identity -> FAIL
12. Legitimate governance PR with authenticated owner authorization -> PASS
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

# Import checker functions directly for unit test mocking
sys.path.insert(0, str(CI_DIR))
import trusted_pr_checker

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
        shutil.copytree(REPO_ROOT / "manifests", tmp_repo / "manifests", dirs_exist_ok=True)
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

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

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

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

    def test_07_unauthorized_trusted_workflow_modification(self):
        """Test 7: Attempt to modify harness-trusted.yml without governance authorization fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            wf_file = tmp_repo / ".github" / "workflows" / "harness-trusted.yml"
            wf_file.write_text("# malicious edit\n", encoding="utf-8")
            self.run_cmd(["git", "add", ".github/workflows/harness-trusted.yml"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch workflow"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

    def test_08_unauthorized_checker_modification(self):
        """Test 8: Attempt to modify trusted_pr_checker.py without governance fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            checker_file = tmp_repo / "ci" / "trusted_pr_checker.py"
            checker_file.write_text("# malicious edit\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/trusted_pr_checker.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch checker"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

    def test_08b_unauthorized_actions_directory_addition(self):
        """Test 8b: Adding an action under .github/actions without governance fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            action_dir = tmp_repo / ".github" / "actions" / "my-action"
            action_dir.mkdir(parents=True, exist_ok=True)
            (action_dir / "action.yml").write_text("name: evil\n", encoding="utf-8")
            self.run_cmd(["git", "add", ".github/actions"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add action"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

    def test_08c_unauthorized_new_ci_script_addition(self):
        """Test 8c: Adding new ci/package.py script without governance fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "ci" / "package.py").write_text("# new packager\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add packaging script"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

    def test_08d_unauthorized_new_manifest_schema_addition(self):
        """Test 8d: Adding new schema under manifests/ without governance fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "manifests" / "new_schema.json").write_text("{}\n", encoding="utf-8")
            self.run_cmd(["git", "add", "manifests/new_schema.json"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add schema"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

    def test_08e_unauthorized_security_policy_modification(self):
        """Test 8e: Modifying SECURITY.md without governance fails."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "SECURITY.md").write_text("# weakened policy\n", encoding="utf-8")
            self.run_cmd(["git", "add", "SECURITY.md"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch SECURITY.md"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo)
            self.assertEqual(cm.exception.code, 1)

    def test_08f_fake_owner_approval_in_candidate_commit(self):
        """Test 8f: Fake approval written inside candidate commit files is rejected."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "ci" / "package.py").write_text("# new packager\n", encoding="utf-8")
            (tmp_repo / "governance_approval.json").write_text('{"decision": "OWNER GOVERNANCE GO"}\n', encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py", "governance_approval.json"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "claim owner approval"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            bad_head_sha = out.strip()

            with self.assertRaises(SystemExit) as cm:
                # Passing empty comments list simulates API having no authenticated owner comment
                trusted_pr_checker.check_admission(base_sha, bad_head_sha, tmp_repo, pr_number=1, mock_comments=[])
            self.assertEqual(cm.exception.code, 1)

    def test_08g_approval_from_non_owner(self):
        """Test 8g: Approval comment from a non-owner account is rejected."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "ci" / "package.py").write_text("# new packager\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add packaging script"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            head_sha = out.strip()

            fake_comments = [{
                "user": {"login": "attacker-user"},
                "author_association": "CONTRIBUTOR",
                "body": f"```governance-authorization\n{{\"decision\": \"OWNER GOVERNANCE GO\", \"repository\": \"skulmakov-oss/Semantic-Dist\", \"pr_number\": 1, \"base_sha\": \"{base_sha}\", \"head_sha\": \"{head_sha}\", \"authorized_paths\": [\"ci/package.py\"]}}\n```"
            }]

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, head_sha, tmp_repo, pr_number=1, mock_comments=fake_comments)
            self.assertEqual(cm.exception.code, 1)

    def test_08h_approval_for_earlier_head_sha(self):
        """Test 8h: Owner approval for an older HEAD does not authorize a new HEAD."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "ci" / "package.py").write_text("# initial\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "step 1"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            old_head_sha = out.strip()

            (tmp_repo / "ci" / "package.py").write_text("# updated\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "step 2"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            new_head_sha = out.strip()

            # Approval was only granted for old_head_sha
            comments = [{
                "user": {"login": "skulmakov-oss"},
                "author_association": "OWNER",
                "body": f"```governance-authorization\n{{\"decision\": \"OWNER GOVERNANCE GO\", \"repository\": \"skulmakov-oss/Semantic-Dist\", \"pr_number\": 1, \"base_sha\": \"{base_sha}\", \"head_sha\": \"{old_head_sha}\", \"authorized_paths\": [\"ci/package.py\"]}}\n```"
            }]

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, new_head_sha, tmp_repo, pr_number=1, mock_comments=comments)
            self.assertEqual(cm.exception.code, 1)

    def test_08i_approval_for_different_pr_number(self):
        """Test 8i: Owner approval for PR #2 cannot authorize PR #1."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "ci" / "package.py").write_text("# initial\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "step 1"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            head_sha = out.strip()

            comments = [{
                "user": {"login": "skulmakov-oss"},
                "author_association": "OWNER",
                "body": f"```governance-authorization\n{{\"decision\": \"OWNER GOVERNANCE GO\", \"repository\": \"skulmakov-oss/Semantic-Dist\", \"pr_number\": 2, \"base_sha\": \"{base_sha}\", \"head_sha\": \"{head_sha}\", \"authorized_paths\": [\"ci/package.py\"]}}\n```"
            }]

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, head_sha, tmp_repo, pr_number=1, mock_comments=comments)
            self.assertEqual(cm.exception.code, 1)

    def test_08j_approval_with_insufficient_path_scope(self):
        """Test 8j: Approval covering only path A fails if candidate also modifies path B."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "ci" / "package.py").write_text("# pkg\n", encoding="utf-8")
            (tmp_repo / "SECURITY.md").write_text("# sec\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py", "SECURITY.md"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "touch both"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            head_sha = out.strip()

            # Authorized only for ci/package.py, NOT SECURITY.md
            comments = [{
                "user": {"login": "skulmakov-oss"},
                "author_association": "OWNER",
                "body": f"```governance-authorization\n{{\"decision\": \"OWNER GOVERNANCE GO\", \"repository\": \"skulmakov-oss/Semantic-Dist\", \"pr_number\": 1, \"base_sha\": \"{base_sha}\", \"head_sha\": \"{head_sha}\", \"authorized_paths\": [\"ci/package.py\"]}}\n```"
            }]

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, head_sha, tmp_repo, pr_number=1, mock_comments=comments)
            self.assertEqual(cm.exception.code, 1)

    def test_08k_revoked_owner_authorization(self):
        """Test 8k: Explicit owner revocation causes immediate rejection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / "ci" / "package.py").write_text("# pkg\n", encoding="utf-8")
            self.run_cmd(["git", "add", "ci/package.py"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "pkg"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            head_sha = out.strip()

            comments = [
                {
                    "user": {"login": "skulmakov-oss"},
                    "author_association": "OWNER",
                    "body": f"```governance-authorization\n{{\"decision\": \"OWNER GOVERNANCE GO\", \"repository\": \"skulmakov-oss/Semantic-Dist\", \"pr_number\": 1, \"base_sha\": \"{base_sha}\", \"head_sha\": \"{head_sha}\", \"authorized_paths\": [\"ci/package.py\"]}}\n```"
                },
                {
                    "user": {"login": "skulmakov-oss"},
                    "author_association": "OWNER",
                    "body": f"REVOKE GOVERNANCE GO {head_sha}"
                }
            ]

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, head_sha, tmp_repo, pr_number=1, mock_comments=comments)
            self.assertEqual(cm.exception.code, 1)

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

            # Should not raise
            trusted_pr_checker.check_admission(base_sha, good_head_sha, tmp_repo)

    def test_09b_candidate_changes_ordinary_launcher_source_only(self):
        """Test 9b: Candidate creating or modifying launcher source passes ordinary admission."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            src_file = tmp_repo / "launcher" / "main.rs"
            src_file.write_text("fn main() {}\n", encoding="utf-8")
            self.run_cmd(["git", "add", "launcher/main.rs"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "launcher source"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            good_head_sha = out.strip()

            # Should not raise
            trusted_pr_checker.check_admission(base_sha, good_head_sha, tmp_repo)

    def test_10_candidate_supplies_executable_script_content(self):
        """Test 10: Candidate supplying shell scripts outside protected paths is admitted as inert data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            exploit_file = tmp_repo / "exploit.sh"
            exploit_file.write_text("#!/bin/bash\necho PWNED > /tmp/pwn\n", encoding="utf-8")
            self.run_cmd(["git", "add", "exploit.sh"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add exploit"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            exploit_head_sha = out.strip()

            # Treated as inert data outside protected control plane -> passes
            trusted_pr_checker.check_admission(base_sha, exploit_head_sha, tmp_repo)

    def test_11_incorrect_base_or_head_identity(self):
        """Test 11: Non-existent base or head SHA fails immediately."""
        with self.assertRaises(SystemExit) as cm:
            trusted_pr_checker.check_admission("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", "1234567890123456789012345678901234567890", REPO_ROOT)
        self.assertEqual(cm.exception.code, 1)

    def test_12_legitimate_owner_authorized_governance_pr(self):
        """Test 12: Candidate modifying workflow with authenticated owner authorization PASSES."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / ".github" / "workflows" / "package-windows.yml").write_text("name: Windows Package\n", encoding="utf-8")
            self.run_cmd(["git", "add", ".github/workflows/package-windows.yml"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add windows package workflow"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            head_sha = out.strip()

            owner_comments = [{
                "user": {"login": "skulmakov-oss"},
                "author_association": "OWNER",
                "body": f"```governance-authorization\n{{\"version\": \"1.0.0\", \"decision\": \"OWNER GOVERNANCE GO\", \"repository\": \"skulmakov-oss/Semantic-Dist\", \"pr_number\": 1, \"base_sha\": \"{base_sha}\", \"head_sha\": \"{head_sha}\", \"authorized_paths\": [\".github/workflows/package-windows.yml\"]}}\n```"
            }]

            # Should succeed without exception
            trusted_pr_checker.check_admission(base_sha, head_sha, tmp_repo, pr_number=1, mock_comments=owner_comments)

    def test_13_pagination_in_fetch_github_comments(self):
        """Test 13: fetch_github_comments traverses Link rel="next" headers until exhausted."""
        from unittest.mock import patch, MagicMock

        page1_data = json.dumps([{"id": 1, "body": "comment 1"}]).encode("utf-8")
        page2_data = json.dumps([{"id": 2, "body": "comment 2"}]).encode("utf-8")

        resp1 = MagicMock()
        resp1.status = 200
        resp1.read.return_value = page1_data
        resp1.headers.get.return_value = '<https://api.github.com/repos/test/repo/issues/1/comments?page=2>; rel="next"'
        resp1.__enter__.return_value = resp1

        resp2 = MagicMock()
        resp2.status = 200
        resp2.read.return_value = page2_data
        resp2.headers.get.return_value = ""
        resp2.__enter__.return_value = resp2

        with patch("urllib.request.urlopen", side_effect=[resp1, resp2]) as mock_urlopen:
            comments = trusted_pr_checker.fetch_github_comments("test/repo", 1, "token")
            self.assertEqual(len(comments), 2)
            self.assertEqual(comments[0]["id"], 1)
            self.assertEqual(comments[1]["id"], 2)
            self.assertEqual(mock_urlopen.call_count, 2)

    def test_14_governance_authorization_schema_validation_rejects_malformed(self):
        """Test 14: Governance block violating schema (missing required field or bad type) fails admission."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_repo, base_sha = self.create_fixture_base_and_candidate(tmp_dir)
            (tmp_repo / ".github" / "workflows" / "package-windows.yml").write_text("name: Windows Package\n", encoding="utf-8")
            self.run_cmd(["git", "add", ".github/workflows/package-windows.yml"], cwd=tmp_repo)
            self.run_cmd(["git", "commit", "-m", "add windows package workflow"], cwd=tmp_repo)
            ret, out, _ = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=tmp_repo)
            head_sha = out.strip()

            # Malformed governance block: missing 'version' and authorized_paths is a mapping instead of array
            malformed_comments = [{
                "user": {"login": "skulmakov-oss"},
                "author_association": "OWNER",
                "body": f"```governance-authorization\n{{\"decision\": \"OWNER GOVERNANCE GO\", \"repository\": \"skulmakov-oss/Semantic-Dist\", \"pr_number\": 1, \"base_sha\": \"{base_sha}\", \"head_sha\": \"{head_sha}\", \"authorized_paths\": {{\"path\": \".github/workflows/package-windows.yml\"}}}}\n```"
            }]

            with self.assertRaises(SystemExit) as cm:
                trusted_pr_checker.check_admission(base_sha, head_sha, tmp_repo, pr_number=1, mock_comments=malformed_comments)
            self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
