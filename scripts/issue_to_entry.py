#!/usr/bin/env python3
"""Convert a GitHub QOTD Issue Form submission to one validated JSON record."""
import argparse
import json
import re
from pathlib import Path

from scripts.build_archive import validate_entry

HEADINGS = {
    "Entry type": "kind",
    "Main topic ID (Follow-up only)": "parent",
    "Date (YYYY-MM-DD)": "date",
    "Time (HH:MM, optional)": "time",
    "Topic": "category",
    "Question": "question",
    "Voting mode": "mode",
    "Participant count (optional)": "participants",
    "Choices and votes": "options",
    "Anonymous vote": "anonymous",
    "Additional notes (optional)": "notes",
}


def _parse_sections(body):
    pieces = re.split(r"^### ([^\n]+)\s*$", body, flags=re.MULTILINE)
    result = {}
    for i in range(1, len(pieces), 2):
        title = pieces[i].strip()
        if title in result:
            raise ValueError(f"Duplicate form section: {title}")
        text = pieces[i + 1].strip()
        result[title] = "" if text in ("_No response_", "No response", "None") else text
    if any(name not in result for name in HEADINGS):
        raise ValueError("Submission does not match the QOTD Issue Form")
    return {key: result[name] for name, key in HEADINGS.items()}


def _parse_choices(lines):
    options = []
    if not lines:
        return options
    for n, line in enumerate(lines.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            title, raw = line.rsplit("|", 1)
            title, raw = title.strip(), raw.strip()
        else:
            title, raw = line, "?"
        if raw in ("?", "—", "-", ""):
            votes = None
        elif re.fullmatch(r"\d{1,7}", raw):
            votes = int(raw)
        else:
            raise ValueError(f"Invalid vote count on choices line {n}; use a number or ?")
        options.append({"text": title, "votes": votes})
    return options


def _parent_id(value):
    value = value.strip()
    if value.startswith("https://github.com/"):
        match = re.fullmatch(r"https://github\.com/[^/]+/[^/]+/issues/(\d+)/?", value)
        if match:
            return "issue-" + match[1]
    if re.fullmatch(r"#\d+", value):
        return "issue-" + value[1:]
    return value


def issue_to_entry(issue):
    if not isinstance(issue, dict) or type(issue.get("number")) is not int:
        raise ValueError("Invalid GitHub issue event")
    fields = _parse_sections(issue.get("body") or "")
    kind = {"Main question": "main", "Follow-up": "followup"}.get(fields["kind"])
    if kind is None:
        raise ValueError("Choose Main question or Follow-up")
    modes = {
        "Single choice": False,
        "Multiple choices": True,
        "Not sure": None,
        "Open-ended (no poll)": None,
    }
    if fields["mode"] not in modes:
        raise ValueError("Unrecognized voting mode")
    anonymous = {"Yes": True, "No": False, "Not sure": None}
    if fields["anonymous"] not in anonymous:
        raise ValueError("Unrecognized anonymous vote response")
    count = fields["participants"]
    if count:
        if not re.fullmatch(r"\d{1,7}", count):
            raise ValueError("Participant count must be a nonnegative integer")
        count = int(count)
    else:
        count = None
    options = _parse_choices(fields["options"])
    if fields["mode"] == "Open-ended (no poll)" and options:
        raise ValueError("Open-ended questions must not have voting choices")
    parent = _parent_id(fields["parent"]) or None
    result = {
        "id": f"issue-{issue['number']}",
        "kind": kind,
        "parentId": parent if kind == "followup" else None,
        "date": fields["date"], "time": fields["time"],
        "category": fields["category"], "question": fields["question"],
        "multipleChoice": modes[fields["mode"]],
        "anonymous": anonymous[fields["anonymous"]],
        "participants": count, "options": options, "notes": fields["notes"],
    }
    if kind == "main" and parent:
        raise ValueError("Main question cannot specify a parent")
    validate_entry(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("event", type=Path, help="Path to the GitHub issues event JSON")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    event = json.loads(args.event.read_text(encoding="utf-8"))
    entry = issue_to_entry(event["issue"])
    if args.output.name != entry["id"] + ".json":
        raise SystemExit("Output filename must match issue ID")
    if args.output.exists():
        raise SystemExit("Target file already exists")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
