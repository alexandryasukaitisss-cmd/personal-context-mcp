import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from personal_context_mcp.core import (
    HEALTH_ENDPOINTS,
    bound_int,
    clip_text,
    health_endpoint_allowed,
    is_safe_session_path,
    redact_text,
    validate_session_id,
)


class SecurityTests(unittest.TestCase):
    def test_redacts_common_credentials_and_home_paths(self):
        source = (
            "Authorization: Bearer super-secret-token-value "
            "api_key='sk-proj-12345678901234567890' password=hunter2 "
            '"passwordHash": "hash-value" "clientId": "client-value" '
            "Cookie: sid=private-value "
            "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY----- "
            "/Users/example/private/file.txt"
        )
        redacted = redact_text(source)
        self.assertNotIn("super-secret-token-value", redacted)
        self.assertNotIn("sk-proj-12345678901234567890", redacted)
        self.assertNotIn("hunter2", redacted)
        self.assertNotIn("hash-value", redacted)
        self.assertNotIn("client-value", redacted)
        self.assertNotIn("sid=private-value", redacted)
        self.assertNotIn("BEGIN PRIVATE KEY", redacted)
        self.assertNotIn("/Users/example/private/file.txt", redacted)

    def test_session_id_validation(self):
        valid = "019f9add-88ef-7932-b0e3-25d339238655"
        self.assertEqual(validate_session_id(valid.upper()), valid)
        for invalid in ("../secret", "not-a-uuid", "", None):
            with self.assertRaises(ValueError):
                validate_session_id(invalid)

    def test_path_must_stay_inside_allowlisted_root_and_not_be_symlink(self):
        root = Path("/tmp/personal-context-codex")
        self.assertTrue(is_safe_session_path(root / "2026" / "session.jsonl", root))
        self.assertFalse(is_safe_session_path(root / ".." / "outside.jsonl", root))

        with TemporaryDirectory() as directory:
            base = Path(directory)
            safe_root = base / "sessions"
            safe_root.mkdir()
            outside = base / "outside.jsonl"
            outside.write_text("not a session", encoding="utf-8")
            escaped = safe_root / "link.jsonl"
            escaped.symlink_to(outside)
            self.assertFalse(is_safe_session_path(escaped, safe_root))

    def test_bounds_are_hard(self):
        self.assertEqual(bound_int(999, 5, 1, 10), 10)
        clipped, truncated, _ = clip_text("x" * 100, 12)
        self.assertTrue(truncated)
        self.assertLessEqual(len(clipped), 12)

    def test_health_allowlist_contains_only_fixed_targets(self):
        self.assertEqual(len(HEALTH_ENDPOINTS), 5)
        for endpoint in HEALTH_ENDPOINTS:
            self.assertTrue(health_endpoint_allowed(endpoint.host, endpoint.port, endpoint.path))
        self.assertFalse(health_endpoint_allowed("127.0.0.1", 2455, "/dashboard"))
        self.assertFalse(health_endpoint_allowed("localhost", 2455, "/health/live"))


if __name__ == "__main__":
    unittest.main()
