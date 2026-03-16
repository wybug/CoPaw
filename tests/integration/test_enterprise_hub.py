# -*- coding: utf-8 -*-
"""Integration tests for Enterprise Skills Hub."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hub_enterprise"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from hub_enterprise.signature import generate_key_pair, SignatureGenerator, SignatureVerifier
from hub_enterprise.storage.skills import SkillStorage
from hub_enterprise.storage.approvals import ApprovalStorage
from hub_enterprise.storage.audit import AuditStorage
from hub_enterprise.models import SkillBundle


class TestSignatureModule(unittest.TestCase):
    """Test signature generation and verification."""

    def setUp(self):
        """Generate test keys."""
        self.private_pem, self.public_pem = generate_key_pair()
        self.test_bundle = {
            "name": "test-skill",
            "content": "# Test Skill\nTest content",
            "version": "1.0.0",
        }

    def test_generate_key_pair(self):
        """Test RSA key pair generation."""
        self.assertIn("-----BEGIN PRIVATE KEY-----", self.private_pem)
        self.assertIn("-----END PRIVATE KEY-----", self.private_pem)
        self.assertIn("-----BEGIN PUBLIC KEY-----", self.public_pem)
        self.assertIn("-----END PUBLIC KEY-----", self.public_pem)

    def test_sign_bundle(self):
        """Test bundle signing."""
        signer = SignatureGenerator(self.private_pem)
        signature = signer.sign_skill_bundle(self.test_bundle)
        self.assertIsInstance(signature, str)
        self.assertGreater(len(signature), 100)

    def test_verify_valid_signature(self):
        """Test valid signature verification."""
        signer = SignatureGenerator(self.private_pem)
        signature = signer.sign_skill_bundle(self.test_bundle)
        verifier = SignatureVerifier(self.public_pem)
        is_valid = verifier.verify_skill_bundle(self.test_bundle, signature)
        self.assertTrue(is_valid)

    def test_verify_tampered_bundle(self):
        """Test that tampered bundles fail verification."""
        signer = SignatureGenerator(self.private_pem)
        signature = signer.sign_skill_bundle(self.test_bundle)
        verifier = SignatureVerifier(self.public_pem)

        tampered_bundle = self.test_bundle.copy()
        tampered_bundle["content"] = "# Tampered Content"

        is_valid = verifier.verify_skill_bundle(tampered_bundle, signature)
        self.assertFalse(is_valid)

    def test_verify_wrong_signature(self):
        """Test that wrong signatures fail verification."""
        verifier = SignatureVerifier(self.public_pem)
        is_valid = verifier.verify_skill_bundle(self.test_bundle, "invalid_signature")
        self.assertFalse(is_valid)


class TestSkillStorage(unittest.TestCase):
    """Test skill storage."""

    def setUp(self):
        """Create temporary storage."""
        import uuid
        self.tmpdir = tempfile.mkdtemp()
        self.storage = SkillStorage(data_dir=self.tmpdir)
        self.test_slug = f"test-skill-{uuid.uuid4().hex[:8]}"
        self.bundle = SkillBundle(
            name="test-skill",
            content="# Test Skill\n\nTest description",
            files={"scripts/test.py": 'print("hello")'},
            version="1.0.0",
        )

    def tearDown(self):
        """Clean up temporary storage."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_pending_skill(self):
        """Test creating a pending skill."""
        slug = self.storage.create_pending(
            slug=self.test_slug,
            name="Test Skill",
            description="A test skill",
            version="1.0.0",
            bundle=self.bundle,
        )
        self.assertEqual(slug, self.test_slug)

    def test_get_skill(self):
        """Test retrieving a skill."""
        self.storage.create_pending(
            slug=self.test_slug,
            name="Test Skill",
            description="A test skill",
            version="1.0.0",
            bundle=self.bundle,
        )
        skill = self.storage.get_by_slug(self.test_slug)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "Test Skill")
        self.assertEqual(skill.status, "pending")

    def test_approve_skill(self):
        """Test approving a skill."""
        self.storage.create_pending(
            slug=self.test_slug,
            name="Test Skill",
            description="A test skill",
            version="1.0.0",
            bundle=self.bundle,
        )
        result = self.storage.approve_skill(self.test_slug, "test-signature", approver="admin")
        self.assertTrue(result)

        skill = self.storage.get_by_slug(self.test_slug)
        self.assertEqual(skill.status, "approved")
        self.assertEqual(skill.signature, "test-signature")

    def test_search_approved_skills(self):
        """Test searching approved skills."""
        self.storage.create_pending(
            slug=self.test_slug,
            name="Test Skill",
            description="A test skill",
            version="1.0.0",
            bundle=self.bundle,
        )
        self.storage.approve_skill(self.test_slug, "test-signature")

        results = self.storage.search(status="approved")
        self.assertGreaterEqual(len(results), 1)
        # Find our test skill
        found = any(r.slug == self.test_slug for r in results)
        self.assertTrue(found)


class TestApprovalStorage(unittest.TestCase):
    """Test approval storage."""

    def setUp(self):
        """Create temporary storage."""
        import uuid
        self.tmpdir = tempfile.mkdtemp()
        self.storage = ApprovalStorage(data_dir=self.tmpdir)
        self.test_slug = f"test-skill-{uuid.uuid4().hex[:8]}"
        self.bundle = SkillBundle(
            name="test-skill",
            content="# Test",
            files={},
            version="1.0.0",
        )

    def tearDown(self):
        """Clean up temporary storage."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_approval(self):
        """Test creating an approval request."""
        approval_id = self.storage.create(self.test_slug, self.bundle, submitter="user1")
        self.assertIsNotNone(approval_id)

    def test_list_pending(self):
        """Test listing pending approvals."""
        self.storage.create(self.test_slug, self.bundle)
        approvals = self.storage.list_pending()
        # Should have at least our test approval
        self.assertGreaterEqual(len(approvals), 1)
        # Check our approval is in the list
        found = any(a.skill_slug == self.test_slug for a in approvals)
        self.assertTrue(found)

    def test_update_status(self):
        """Test updating approval status."""
        approval_id = self.storage.create(self.test_slug, self.bundle)
        result = self.storage.update_status(approval_id, "approved", reviewer="admin")
        self.assertTrue(result)

        approval = self.storage.get(approval_id)
        self.assertEqual(approval.status, "approved")


class TestCopawEnterpriseMode(unittest.TestCase):
    """Test CoPaw enterprise mode integration."""

    def setUp(self):
        """Save original environment."""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        # Reload modules to pick up env changes
        import importlib
        from copaw.agents import skills_hub
        importlib.reload(skills_hub)

    def test_is_enterprise_mode_false(self):
        """Test enterprise mode detection when not configured."""
        from copaw.agents import skills_hub
        import importlib
        importlib.reload(skills_hub)

        self.assertFalse(skills_hub._is_enterprise_mode())

    def test_is_enterprise_mode_true(self):
        """Test enterprise mode detection when configured."""
        _, public_pem = generate_key_pair()
        os.environ["COPAW_SKILLS_HUB_PUBLIC_KEY"] = public_pem

        from copaw.agents import skills_hub
        import importlib
        importlib.reload(skills_hub)

        self.assertTrue(skills_hub._is_enterprise_mode())

    def test_enforce_enterprise_mode_blocks_clawhub(self):
        """Test that enterprise mode blocks clawhub.ai access."""
        private_pem, public_pem = generate_key_pair()
        os.environ["COPAW_SKILLS_HUB_BASE_URL"] = "https://clawhub.ai"
        os.environ["COPAW_SKILLS_HUB_PUBLIC_KEY"] = public_pem

        from copaw.agents import skills_hub
        import importlib
        importlib.reload(skills_hub)

        with self.assertRaises(ValueError) as context:
            skills_hub._enforce_enterprise_mode()
        self.assertIn("prohibited", str(context.exception).lower())

    def test_enforce_enterprise_mode_allows_custom_hub(self):
        """Test that enterprise mode allows custom hub."""
        private_pem, public_pem = generate_key_pair()
        os.environ["COPAW_SKILLS_HUB_BASE_URL"] = "http://enterprise-hub:9090"
        os.environ["COPAW_SKILLS_HUB_PUBLIC_KEY"] = public_pem

        from copaw.agents import skills_hub
        import importlib
        importlib.reload(skills_hub)

        # Should not raise
        skills_hub._enforce_enterprise_mode()

    def test_verify_signature(self):
        """Test signature verification in CoPaw."""
        private_pem, public_pem = generate_key_pair()
        os.environ["COPAW_SKILLS_HUB_PUBLIC_KEY"] = public_pem

        from copaw.agents import skills_hub
        from hub_enterprise.signature import SignatureGenerator
        import importlib
        importlib.reload(skills_hub)

        test_bundle = {"name": "test", "content": "# Test", "references": {}, "scripts": {}}
        signer = SignatureGenerator(private_pem)
        signature = signer.sign_skill_bundle(test_bundle)

        is_valid = skills_hub._verify_bundle_signature(test_bundle, signature)
        self.assertTrue(is_valid)


class TestIntegration(unittest.TestCase):
    """Integration tests with server."""

    @classmethod
    def setUpClass(cls):
        """Start test server."""
        cls.tmpdir = tempfile.mkdtemp()
        cls.private_pem, cls.public_pem = generate_key_pair()

        env = os.environ.copy()
        env["HUB_HOST"] = "localhost"
        env["HUB_PORT"] = "9995"
        env["HUB_DATA_DIR"] = cls.tmpdir
        env["HUB_PRIVATE_KEY"] = cls.private_pem

        cls.server_proc = subprocess.Popen(
            [sys.executable, "-m", "hub_enterprise"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="hub_enterprise"
        )
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        """Stop test server."""
        cls.server_proc.terminate()
        try:
            cls.server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server_proc.kill()

        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_health_check(self):
        """Test server health endpoint."""
        import urllib.request
        response = urllib.request.urlopen("http://localhost:9995/health", timeout=5)
        data = json.loads(response.read())
        self.assertEqual(data["status"], "healthy")

    def test_submit_skill(self):
        """Test skill submission."""
        import urllib.request
        import uuid
        skill_slug = f"test-submit-{uuid.uuid4().hex[:8]}"
        skill_data = {
            "slug": skill_slug,
            "name": "Test Submit",
            "description": "Test",
            "content": "# Test",
            "version": "1.0.0",
        }
        data = json.dumps(skill_data).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:9995/api/v1/skills/submit",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        response = urllib.request.urlopen(req, timeout=5)
        result = json.loads(response.read())
        self.assertIn("approval_id", result)

    def test_search_skills(self):
        """Test skill search."""
        import urllib.request
        response = urllib.request.urlopen(
            "http://localhost:9995/api/v1/search?q=test&limit=10", timeout=5
        )
        result = json.loads(response.read())
        self.assertIn("items", result)


if __name__ == "__main__":
    unittest.main()
