from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from . import course_status
except ImportError:
    import course_status


class CourseStatusTests(unittest.TestCase):
    def test_roster_requires_expected_columns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roster.csv"
            path.write_text(
                "student_id,gitea_login,repo_owner,repo_name\n"
                "1,s01,s01,machine-learning-2026\n",
                encoding="utf-8",
            )
            self.assertEqual(course_status.read_roster(path)[0]["gitea_login"], "s01")

    def test_mapping_covers_two_core_and_thirty_skill_lessons(self) -> None:
        self.assertEqual(len(course_status.LESSONS), 32)
        self.assertEqual(course_status.LESSONS[:2], ["C01", "C02"])
        self.assertEqual(course_status.LESSONS[-1], "S30")
        self.assertEqual(course_status.TAG_BY_LESSON["S30"], "v2-l32-final")
        self.assertEqual(course_status.STATUS_FILE_BY_TAG["v2-l01-final"], "lessons/C01/submission.json")

    @patch.object(course_status, "api_get")
    def test_green_requires_signed_complete_and_success_status(self, api_get) -> None:
        signed = base64.b64encode(
            json.dumps({"status": "complete", "lesson_id": "S01"}).encode("utf-8")
        ).decode("ascii")
        api_get.side_effect = [
            (200, {"name": "machine-learning-2026"}),
            (200, [{"ref": "refs/tags/v2-l03-final"}]),
            (200, {"content": signed}),
            (200, {"state": "success", "sha": "1234567890abcdef"}),
        ]
        result = course_status.status_for(
            "https://example.test/gitea", "token",
            {"repo_owner": "s01", "repo_name": "machine-learning-2026"}, "S01"
        )
        self.assertEqual(result["light"], "GREEN")
        self.assertEqual(result["signed"], "complete")
        self.assertEqual(result["sha"], "1234567890abcdef")

    @patch.object(course_status, "api_get")
    def test_wrong_lesson_cannot_be_green(self, api_get) -> None:
        signed = base64.b64encode(
            json.dumps({"status": "complete", "lesson_id": "S02"}).encode("utf-8")
        ).decode("ascii")
        api_get.side_effect = [
            (200, {}), (200, [{}]), (200, {"content": signed}),
            (200, {"state": "success", "sha": "abc"}),
        ]
        result = course_status.status_for(
            "https://example.test", "token",
            {"repo_owner": "s01", "repo_name": "course"}, "S01"
        )
        self.assertEqual(result["light"], "RED")
        self.assertEqual(result["signed"], "wrong_lesson")

    @patch.object(course_status, "api_get")
    def test_success_ci_is_red_when_submission_not_complete(self, api_get) -> None:
        signed = base64.b64encode(
            json.dumps({"status": "in_progress", "lesson_id": "S01"}).encode("utf-8")
        ).decode("ascii")
        api_get.side_effect = [
            (200, {}), (200, [{}]), (200, {"content": signed}),
            (200, {"state": "success", "sha": "abc"}),
        ]
        result = course_status.status_for(
            "https://example.test", "token",
            {"repo_owner": "s01", "repo_name": "course"}, "S01"
        )
        self.assertEqual(result["light"], "RED")
        self.assertEqual(result["signed"], "in_progress")

    @patch.object(course_status, "api_get")
    def test_missing_tag_is_red(self, api_get) -> None:
        api_get.side_effect = [(200, {}), (404, None)]
        result = course_status.status_for(
            "https://example.test", "token",
            {"repo_owner": "s01", "repo_name": "course"}, "S01"
        )
        self.assertEqual(result["light"], "RED")

    @patch.object(course_status, "api_get")
    def test_missing_repo_has_complete_output_shape(self, api_get) -> None:
        api_get.return_value = (404, None)
        result = course_status.status_for(
            "https://example.test", "token",
            {"repo_owner": "s01", "repo_name": "course"}, "S01"
        )
        self.assertEqual(result["light"], "RED")
        self.assertEqual(result["signed"], "-")

    def test_unknown_lesson_rejected(self) -> None:
        with self.assertRaises(ValueError):
            course_status.status_for("https://example.test", "token", {"repo_owner": "x", "repo_name": "y"}, "S31")


if __name__ == "__main__":
    unittest.main()
