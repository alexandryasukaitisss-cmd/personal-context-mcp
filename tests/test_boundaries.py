import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from personal_context_mcp.core import (
    ContextService,
    HealthEndpoint,
    ReadOnlyMempalace,
    _check_health_endpoint,
    _configured_path,
    _source_hit,
    clip_text,
    redact_text,
)


class BoundaryTests(unittest.TestCase):
    def test_clip_is_exact_and_marks_truncation(self):
        clipped, truncated, original = clip_text("abcdefghijklmnopqrstuvwxyz", 10)
        self.assertTrue(truncated)
        self.assertEqual(original, 26)
        self.assertLessEqual(len(clipped), 10)

    def test_empty_and_tiny_limits_do_not_overrun(self):
        for limit in (0, 1, 5, 11):
            clipped, _, _ = clip_text("abcdefghijklmnopqrstuvwxyz", limit)
            self.assertLessEqual(len(clipped), limit)

    def test_clip_redacts_before_counting(self):
        clipped, _, _ = clip_text("password=hunter2", 100)
        self.assertNotIn("hunter2", clipped)
        self.assertIn("[REDACTED]", clipped)

    def test_home_path_redaction_covers_linux_and_macos(self):
        for path in ("/Users/alice/private", "/home/alice/private"):
            self.assertNotIn(path, redact_text(path))

    def test_search_rejects_empty_query_and_invalid_source(self):
        service = ContextService(mempalace=ReadOnlyMempalace(Path("/nonexistent")))
        self.assertEqual(service.context_search("   "), {"error": "query_required"})
        self.assertEqual(service.context_search("x", source="other"), {"error": "invalid_source"})

    def test_search_bounds_are_applied_even_when_empty(self):
        service = ContextService(mempalace=ReadOnlyMempalace(Path("/nonexistent")))
        result = service.context_search("x", source="mempalace", limit=999, max_chars=999999)
        self.assertEqual(result["limit"], 10)
        self.assertEqual(result["max_chars"], 6000)
        self.assertEqual(result["results"], [])

    def test_session_read_rejects_non_uuid_before_touching_disk(self):
        service = ContextService(mempalace=ReadOnlyMempalace(Path("/nonexistent")))
        self.assertEqual(service.context_read_session("../../etc/passwd"), {"error": "invalid_session_id"})
        self.assertEqual(service.context_read_session("019f9add-88ef-7932-b0e3-25d339238655", 0).get("error"), "session_not_found_or_ambiguous")

    def test_sources_are_read_only_and_do_not_expose_paths(self):
        service = ContextService(mempalace=ReadOnlyMempalace(Path("/nonexistent")))
        result = service.context_sources()
        self.assertTrue(result["read_only"])
        self.assertIn("untrusted_data_policy", result)
        serialized = str(result)
        self.assertNotIn("/nonexistent", serialized)

    def test_source_hit_marks_untrusted_and_drops_path_metadata(self):
        hit = _source_hit(
            "codex",
            "text",
            20,
            title="Title",
            session_id="019f9add-88ef-7932-b0e3-25d339238655",
            metadata={"wing": "work", "path": "/secret/path"},
        )
        self.assertTrue(hit["untrusted"])
        self.assertNotIn("path", hit["metadata"])
        self.assertEqual(hit["metadata"]["wing"], "work")

    def test_health_probe_blocks_an_unlisted_endpoint_without_a_socket(self):
        result = _check_health_endpoint(HealthEndpoint("bad", "example.com", 80, "/health"))
        self.assertEqual(result, {"name": "bad", "status": "blocked"})

    def test_configured_path_expands_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.dict(os.environ, {"PERSONAL_CONTEXT_TEST_PATH": directory}):
                self.assertEqual(_configured_path("PERSONAL_CONTEXT_TEST_PATH", Path("/default")), Path(directory))


if __name__ == "__main__":
    unittest.main()
