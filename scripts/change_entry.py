#!/usr/bin/env python3
"""Apply a QOTD edit/delete *only to a review branch*, from a GitHub Issue Form.

The GitHub workflow opens a PR from the modified files. This script does not
publish, merge or authorize anything.
"""
import argparse
import json
import re
from pathlib import Path

from scripts.build_archive import ID_PATTERN, build_archive, validate_entry
from scripts.issue_to_entry import _parse_choices


def _sections(body):
    pieces = re.split(r"^### ([^\n]+)\s*$", body or "", flags=re.MULTILINE)
    sections = {}
    for i in range(1, len(pieces), 2):
        label = pieces[i].strip()
        if label in sections:
            raise ValueError(f"Duplicate form field: {label}")
        value = pieces[i + 1].strip()
        sections[label] = "" if value in ("_No response_", "No response") else value
    return sections


def _yes_no(value, field):
    if value not in ("Yes", "No"):
        raise ValueError(f"{field} must be Yes or No")
    return value == "Yes"


def change_entry(issue, mode, directory):
    """Validate and perform one change on local source files for a PR."""
    if mode not in ("edit", "delete"):
        raise ValueError("Unsupported change mode")
    if not isinstance(issue, dict) or type(issue.get("number")) is not int:
        raise ValueError("Missing GitHub issue number")
    values = _sections(issue.get("body"))
    entry_id = values.get("Entry ID", "")
    if not ID_PATTERN.fullmatch(entry_id):
        raise ValueError("Invalid entry ID")
    path = directory / (entry_id + ".json")
    if not path.is_file():
        raise ValueError(f"No entry exists for ID {entry_id}")
    original = json.loads(path.read_text(encoding="utf-8"))
    validate_entry(original)
    if original["id"] != entry_id or original["kind"] != "main":
        raise ValueError("Only an existing main question can be changed")
    expected_question = values.get("Current question (verification)", "").strip()
    if expected_question != original["question"].strip():
        raise ValueError("The original question has changed. Refresh the form and retry.")

    if mode == "delete":
        if not values.get("Reason for deletion", "").strip():
            raise ValueError("A reason for deletion is required")
        remaining = []
        for filename in directory.glob("*.json"):
            if filename != path:
                remaining.append(json.loads(filename.read_text(encoding="utf-8")))
        if remaining:
            build_archive(remaining)  # Reject dangling parent references.
        path.unlink()
        return entry_id

    for label in ("Question", "Date (YYYY-MM-DD)", "Allow multiple answers? (Yes/No)",
                  "Original poll anonymous? (Yes/No)", "Choices and votes"):
        if label not in values:
            raise ValueError(f"Missing field: {label}")
    choices = _parse_choices(values["Choices and votes"])
    updated = {
        **original,
        "question": values["Question"],
        "date": values["Date (YYYY-MM-DD)"],
        "time": values.get("Time (HH:MM, optional)", ""),
        "multipleChoice": _yes_no(values["Allow multiple answers? (Yes/No)"], "Voting mode")
            if choices else None,
        "anonymous": _yes_no(values["Original poll anonymous? (Yes/No)"], "Anonymity"),
        "participants": None,
        "options": choices,
    }
    validate_entry(updated)
    if updated == original:
        raise ValueError("No changes to this question")
    # Historical sourcePolls remain unchanged so their original evidence
    # survives a reviewed correction to the canonical public question.
    path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return entry_id


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", type=Path)
    parser.add_argument("--mode", required=True, choices=("edit", "delete"))
    parser.add_argument("--source", type=Path, default=Path("entries"))
    args = parser.parse_args()
    event = json.loads(args.event.read_text(encoding="utf-8"))
    print(f"Prepared {args.mode} of {change_entry(event['issue'], args.mode, args.source)}")


if __name__ == "__main__":
    main()
