#!/usr/bin/env python3
"""Validate reviewed entry files and build the static QOTD archive.

The source of truth is entries/*.json. No server, spreadsheet or external
database is required. Called locally and in the Pages deployment workflow.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,90}$")
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def validate_entry(item):
    if not isinstance(item, dict):
        raise ValueError("Entry must be an object")
    entry_id = item.get("id")
    if not isinstance(entry_id, str) or not ID_PATTERN.fullmatch(entry_id):
        raise ValueError(f"Invalid entry ID: {entry_id!r}")
    kind = item.get("kind")
    if kind not in ("main", "followup"):
        raise ValueError(f"{entry_id}: invalid kind")
    parent_id = item.get("parentId")
    if kind == "followup":
        if not isinstance(parent_id, str) or not ID_PATTERN.fullmatch(parent_id):
            raise ValueError(f"{entry_id}: follow-up needs parentId")
    elif parent_id is not None:
        raise ValueError(f"{entry_id}: main question cannot have parentId")
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", item["date"]):
            raise ValueError("Incorrect date format")
        date.fromisoformat(item["date"])
    except (KeyError, ValueError, TypeError) as error:
        raise ValueError(f"{entry_id}: invalid date") from error
    time = item.get("time", "")
    if not isinstance(time, str) or (time and not TIME_PATTERN.fullmatch(time)):
        raise ValueError(f"{entry_id}: invalid time")
    for field, limit in (("question", 1500), ("category", 64)):
        value = item.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError(f"{entry_id}: invalid {field}")
    for field in ("multipleChoice", "anonymous"):
        if item.get(field) is not None and not isinstance(item.get(field), bool):
            raise ValueError(f"{entry_id}: invalid {field}")
    participants = item.get("participants")
    if participants is not None and (
        type(participants) is not int or not 0 <= participants <= 1000000
    ):
        raise ValueError(f"{entry_id}: invalid participants")
    options = item.get("options")
    if not isinstance(options, list) or len(options) > 50:
        raise ValueError(f"{entry_id}: options must be a list of up to 50")
    seen = set()
    for option in options:
        if not isinstance(option, dict):
            raise ValueError(f"{entry_id}: invalid option")
        name, votes = option.get("text"), option.get("votes")
        if not isinstance(name, str) or not name.strip() or len(name) > 400:
            raise ValueError(f"{entry_id}: invalid option text")
        if name.casefold().strip() in seen:
            raise ValueError(f"{entry_id}: duplicate option")
        seen.add(name.casefold().strip())
        if votes is not None and (type(votes) is not int or not 0 <= votes <= 1000000):
            raise ValueError(f"{entry_id}: invalid vote count")
    notes = item.get("notes", "")
    if not isinstance(notes, str) or len(notes) > 2000:
        raise ValueError(f"{entry_id}: invalid notes")
    return item


def _present(item):
    result = {key: item.get(key) for key in (
        "id", "date", "time", "category", "question", "multipleChoice",
        "anonymous", "notes"
    )}
    result["time"] = result["time"] or ""
    result["notes"] = result["notes"] or ""
    result["options"] = [{"text": x["text"], "votes": x["votes"]}
                         for x in item["options"]]
    if item.get("participants") is not None:
        result["participants"] = item["participants"]
        result["participationSource"] = "provided"
    elif item.get("multipleChoice") is False and item["options"] and all(
        x["votes"] is not None for x in item["options"]
    ):
        result["participants"] = sum(x["votes"] for x in item["options"])
        result["participationSource"] = "single-choice-total"
    else:
        result["participants"] = None
        result["participationSource"] = "unknown"
    return result


def build_archive(entries):
    lookup = {}
    for item in entries:
        validate_entry(item)
        if item["id"] in lookup:
            raise ValueError(f"Duplicate ID: {item['id']}")
        lookup[item["id"]] = item
    groups = {}
    for item in entries:
        if item["kind"] == "main":
            groups[item["id"]] = {**_present(item), "followups": []}
    for item in entries:
        if item["kind"] != "followup":
            continue
        parent = lookup.get(item["parentId"])
        if not parent or parent["kind"] != "main":
            raise ValueError(f"{item['id']}: missing or invalid main question parent")
        groups[item["parentId"]]["followups"].append(_present(item))
    for group in groups.values():
        group["followups"].sort(key=lambda r: (r["date"], r["time"], r["id"]))
    questions = sorted(groups.values(), key=lambda r: (
        r["date"], r["time"], r["id"]), reverse=True)
    return {
        "meta": {
            "timezone": "Europe/Berlin",
            "topicCount": len(questions),
            "pollCount": sum(bool(x["options"]) for x in entries),
            "entryCount": len(entries),
            "coverageNote": "Reviewed submissions only. Unknown values are not zero.",
        },
        "questions": questions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("entries"))
    parser.add_argument("--output", type=Path, default=Path("data/qotd.json"))
    args = parser.parse_args()
    source = args.source
    files = sorted(source.glob("*.json"))
    if not files:
        raise SystemExit(f"No source records in {source}")
    entries = []
    for filename in files:
        try:
            item = json.loads(filename.read_text(encoding="utf-8"))
            validate_entry(item)
            if filename.stem != item["id"]:
                raise ValueError("File name and entry ID differ")
            entries.append(item)
        except (ValueError, KeyError, TypeError) as error:
            raise SystemExit(f"{filename}: {error}") from error
    output = build_archive(entries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"Built {len(output['questions'])} topics from {len(entries)} records -> {args.output}")


if __name__ == "__main__":
    main()
