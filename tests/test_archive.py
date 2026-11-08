import unittest
import json
from pathlib import Path

from scripts.build_archive import build_archive, validate_entry


def record(id="issue-1", **overrides):
    r = {
        "id": id, "kind": "main", "parentId": None,
        "date": "2026-11-07", "time": "20:10",
        "question": "How many tabs?", "multipleChoice": False,
        "participants": None, "anonymous": True,
        "options": [{"text": "Few", "votes": 4}, {"text": "Many", "votes": 6}],
        "notes": "",
    }
    r.update(overrides)
    return r


class ArchiveTests(unittest.TestCase):
    def test_grouping_and_single_choice_participants(self):
        parent = record()
        follow = record("issue-2", kind="followup", parentId="issue-1",
                        question="Why?", multipleChoice=True,
                        options=[{"text": "Work", "votes": 8},
                                 {"text": "Fun", "votes": 6}])
        data = build_archive([follow, parent])
        self.assertEqual(len(data["questions"]), 1)
        q = data["questions"][0]
        self.assertIsNone(q["participants"])
        self.assertEqual(q["participationSource"], "unknown")
        self.assertEqual(len(q["options"]), 4)
        self.assertEqual([x["votes"] for x in q["options"]], [4, 6, 8, 6])
        self.assertNotIn("followups", q)
        self.assertEqual(data["meta"]["questionCount"], 1)
        self.assertEqual(data["meta"]["sourcePollCount"], 2)

    def test_missing_parent_rejected(self):
        follow = record(kind="followup", parentId="issue-missing")
        with self.assertRaises(ValueError):
            build_archive([follow])

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            build_archive([record(), record()])

    def test_unverified_vote_not_zero(self):
        q = record(multipleChoice=None, options=[{"text": "A", "votes": None}])
        data = build_archive([q])["questions"][0]
        self.assertIsNone(data["participants"])
        self.assertIsNone(data["options"][0]["votes"])

    def test_negative_votes_rejected(self):
        with self.assertRaises(ValueError):
            validate_entry(record(options=[{"text": "A", "votes": -1}]))

    def test_open_ended_supported(self):
        data = build_archive([record(multipleChoice=None, options=[])])
        self.assertEqual(len(data["questions"][0]["options"]), 0)

    def test_followup_cannot_have_followup_parent(self):
        with self.assertRaises(ValueError):
            build_archive([
                record(), record("issue-2", kind="followup", parentId="issue-1"),
                record("issue-3", kind="followup", parentId="issue-2"),
            ])

    def test_historic_split_polls_are_one_record_each(self):
        root = Path(__file__).resolve().parents[1] / "entries"
        sources = {p.stem: json.loads(p.read_text(encoding="utf-8"))
                   for p in root.glob("*.json")}
        # Future reviewed deletions must not break the test suite.
        for entry_id, source_count in (
            ("historic-70756", 2),
            ("historic-51770", 3),
        ):
            if entry_id in sources:
                self.assertEqual(len(sources[entry_id]["sourcePolls"]), source_count)
        data = build_archive(list(sources.values()))
        self.assertEqual(data["meta"]["questionCount"], len(data["questions"]))
        self.assertTrue(all("followups" not in x for x in data["questions"]))


if __name__ == "__main__":
    unittest.main()
