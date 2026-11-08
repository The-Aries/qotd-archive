import json
import tempfile
import unittest
from pathlib import Path

from scripts.change_entry import change_entry


ORIGINAL = {
    "id": "historic-12345", "kind": "main", "parentId": None,
    "date": "2026-11-07", "time": "12:30",
    "question": "Original poll?", "multipleChoice": False, "anonymous": None,
    "participants": 30, "options": [
        {"text": "Yes", "votes": 20}, {"text": "No", "votes": 10}
    ], "notes": "verified",
    "sourcePolls": [{
        "id": "historic-12345", "question": "Original poll?", "date": "2026-11-07",
        "options": [{"text": "Yes", "votes": 20}, {"text": "No", "votes": 10}],
    }],
}


def form(**fields):
    return {"number": 246, "body": "\n\n".join(
        "### " + label + "\n\n" + value for label, value in fields.items()
    )}


def edit_form():
    return form(**{
        "Entry ID": "historic-12345",
        "Current question (verification)": "Original poll?",
        "Question": "Corrected poll?",
        "Date (YYYY-MM-DD)": "2026-11-07",
        "Time (HH:MM, optional)": "12:30",
        "Allow multiple answers? (Yes/No)": "Yes",
        "Original poll anonymous? (Yes/No)": "No",
        "Choices and votes": "Yes | 21\nNo | 0\nMaybe | ?",
        "Reason for change (optional)": "Original count was wrong",
    })


def delete_form():
    return form(**{
        "Entry ID": "historic-12345",
        "Current question (verification)": "Original poll?",
        "Reason for deletion": "Duplicate poll",
    })


class ChangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.path = self.directory / "historic-12345.json"
        self.path.write_text(json.dumps(ORIGINAL))

    def test_edit_changes_question_and_vote_counts_not_source_evidence(self):
        self.assertEqual(change_entry(edit_form(), "edit", self.directory),
                         "historic-12345")
        updated = json.loads(self.path.read_text())
        self.assertEqual(updated["question"], "Corrected poll?")
        self.assertTrue(updated["multipleChoice"])
        self.assertFalse(updated["anonymous"])
        self.assertEqual([x["votes"] for x in updated["options"]], [21, 0, None])
        self.assertIsNone(updated["participants"])
        self.assertEqual(updated["sourcePolls"], ORIGINAL["sourcePolls"])

    def test_delete_removes_only_target(self):
        another = self.directory / "historic-99999.json"
        another.write_text(json.dumps({**ORIGINAL, "id": "historic-99999"}))
        change_entry(delete_form(), "delete", self.directory)
        self.assertFalse(self.path.exists())
        self.assertTrue(another.exists())

    def test_stale_edit_and_delete_refused(self):
        for issue, mode in ((edit_form(), "edit"), (delete_form(), "delete")):
            issue["body"] = issue["body"].replace("Original poll?", "Old wrong title")
            with self.assertRaises(ValueError):
                change_entry(issue, mode, self.directory)
        self.assertTrue(self.path.exists())

    def test_path_traversal_and_missing_entry_refused(self):
        for target in ("../../another", "historic-missing"):
            issue = delete_form()
            issue["body"] = issue["body"].replace("historic-12345", target)
            with self.assertRaises(ValueError):
                change_entry(issue, "delete", self.directory)

    def test_delete_requires_reason(self):
        issue = delete_form()
        issue["body"] = issue["body"].replace("Duplicate poll", "_No response_")
        with self.assertRaises(ValueError):
            change_entry(issue, "delete", self.directory)

    def test_invalid_edit_preserves_original(self):
        issue = edit_form()
        issue["body"] = issue["body"].replace("Maybe | ?", "Maybe | -4")
        with self.assertRaises(ValueError):
            change_entry(issue, "edit", self.directory)
        self.assertEqual(json.loads(self.path.read_text()), ORIGINAL)


if __name__ == "__main__":
    unittest.main()
