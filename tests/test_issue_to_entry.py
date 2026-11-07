import unittest

from scripts.issue_to_entry import issue_to_entry


BODY = """### Entry type

Main question

### Main topic ID (Follow-up only)

_No response_

### Date (YYYY-MM-DD)

2026-11-07

### Time (HH:MM, optional)

20:05

### Question

What is your preferred browser?

### Voting mode

Multiple choices

### Participant count (optional)

_No response_

### Choices and votes

Firefox | 12
Chrome | 8
Safari | ?

### Anonymous vote

Not sure

### Additional notes (optional)

Sample poll
"""


class FormTests(unittest.TestCase):
    def test_plain_issue_becomes_structured_record(self):
        entry = issue_to_entry({"number": 123, "body": BODY})
        self.assertEqual(entry["id"], "issue-123")
        self.assertEqual(entry["date"], "2026-11-07")
        self.assertTrue(entry["multipleChoice"])
        self.assertIsNone(entry["participants"])
        self.assertEqual(entry["options"][-1]["votes"], None)
        self.assertEqual(len(entry["options"]), 3)

    def test_followup_requires_parent(self):
        with self.assertRaises(ValueError):
            issue_to_entry({"number": 124, "body": BODY.replace(
                "Main question", "Follow-up", 1)})

    def test_followup_parent_link(self):
        entry = issue_to_entry({"number": 124, "body": BODY.replace(
            "Main question", "Follow-up", 1).replace(
            "### Main topic ID (Follow-up only)\n\n_No response_",
            "### Main topic ID (Follow-up only)\n\nissue-123")})
        self.assertEqual(entry["kind"], "followup")
        self.assertEqual(entry["parentId"], "issue-123")

    def test_malformed_date_rejected(self):
        with self.assertRaises(ValueError):
            issue_to_entry({"number": 125, "body": BODY.replace(
                "2026-11-07", "2026-02-30")})

    def test_negative_votes_rejected(self):
        with self.assertRaises(ValueError):
            issue_to_entry({"number": 126, "body": BODY.replace(
                "Firefox | 12", "Firefox | -12")})


if __name__ == "__main__":
    unittest.main()
