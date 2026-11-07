#!/usr/bin/env python3
"""Read-only extraction of WhatsApp poll candidates and quoted poll previews.

Poll messages are recognizable locally by message type 46, but their question
and answer choices are not stored in ZWAMESSAGE.ZTEXT. When a later message
quotes a poll, its ZWAMEDIAITEM.ZMETADATA can contain a plaintext protobuf
preview of the question and options. This script collects those previews
without copying messages or participant identities to a public file.
"""

import argparse
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

DEFAULT_DB = Path.home() / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def varint(raw, start):
    number = 0
    for index in range(start, min(len(raw), start + 10)):
        byte = raw[index]
        number |= (byte & 127) << (7 * (index - start))
        if not byte & 128:
            return number, index + 1
    return None, start


def human_text(raw):
    try:
        value = raw.decode("utf-8")
    except UnicodeError:
        return None
    if len(value) < 3 or len(value) > 2000:
        return None
    if sum(c.isprintable() or c in "\r\n\t" for c in value) < len(value) * 0.97:
        return None
    if len(value.strip()) < 3:
        return None
    return value.strip()


def candidates(raw, field_byte, start=0, end=None):
    """Return plausible byte-length-delimited strings beginning with a tag."""
    if end is None:
        end = len(raw)
    results = []
    pos = start
    while pos < end:
        i = raw.find(bytes([field_byte]), pos, end)
        if i < 0:
            break
        size, after = varint(raw, i + 1)
        if size is not None and after + size <= end:
            value = human_text(raw[after:after + size])
            if value:
                results.append((i, after + size, value))
        pos = i + 1
    return results


def parse_preview(raw, stanza):
    idx = raw.find(stanza)
    if idx < 0:
        return None
    # Quoted poll previews have protobuf tag 0x12 for title and repeated
    # 0x1a embedded messages containing 0x0a option text fields.
    titles = candidates(raw, 0x12, idx + len(stanza))
    if not titles:
        return None
    choices = []
    ranked = []
    for start, end, title in titles:
        score = (4 if "?" in title or "question" in title.lower() else 0) + min(len(title), 200) / 200
        if "@" in title and len(title) < 40:
            score -= 6
        if len(title) >= 6:
            ranked.append((score, start, end, title))
    if not ranked:
        return None
    _, pos, end, title = max(ranked, key=lambda r: (r[0], -r[1]))
    cursor = end
    while cursor < len(raw) and raw[cursor] == 0x1A:
        size, begin = varint(raw, cursor + 1)
        if size is None or begin + size > len(raw):
            break
        part = raw[begin:begin + size]
        opts = candidates(part, 0x0A)
        opts = [(i, value) for i, _, value in opts if i == 0]
        if not opts:
            break
        choices.append(opts[0][1])
        cursor = begin + size
    return {"question": title, "options": choices}


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--chat", required=True, help="Unique substring of a group chat name")
    arg.add_argument("--database", type=Path, default=DEFAULT_DB)
    arg.add_argument("--output", type=Path, default=Path("private/poll_catalog.json"))
    arg.add_argument("--summary", type=Path, default=Path("private/poll_catalog.md"))
    options = arg.parse_args()
    db = options.database.expanduser().resolve(strict=True)
    connection = sqlite3.connect("file:" + quote(str(db), safe="/") + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only=ON")
    chats = connection.execute(
        "SELECT Z_PK FROM ZWACHATSESSION WHERE ZPARTNERNAME LIKE ?",
        ("%" + options.chat + "%",),
    ).fetchall()
    if len(chats) != 1:
        raise SystemExit("Group name must match exactly one chat.")
    poll_rows = connection.execute(
        """SELECT Z_PK, ZSTANZAID, ZMESSAGEDATE, ZISFROMME
           FROM ZWAMESSAGE
           WHERE ZCHATSESSION=? AND ZMESSAGETYPE=46
           ORDER BY ZMESSAGEDATE DESC""",
        (chats[0][0],),
    ).fetchall()
    records = []
    by_token = {}
    for key, stanza, time, from_me in poll_rows:
        local = (EPOCH + timedelta(seconds=time)).astimezone(ZoneInfo("Europe/Berlin"))
        record = {
            "localRecordId": key,
            "localDateTime": local.isoformat(timespec="seconds"),
            "fromThisAccount": bool(from_me),
            "question": None,
            "options": None,
            "previewEvidenceCount": 0,
            "verification": "unverified",
            "nearbyQotdText": None,
            "qotdMarker": "undetermined",
        }
        records.append(record)
        if stanza:
            by_token[stanza.encode("ascii")] = record
    for metadata, in connection.execute(
        "SELECT ZMETADATA FROM ZWAMEDIAITEM WHERE length(ZMETADATA)>100"
    ):
        if not metadata:
            continue
        for stanza, record in by_token.items():
            if stanza not in metadata:
                continue
            record["previewEvidenceCount"] += 1
            preview = parse_preview(metadata, stanza)
            if preview and (
                record["question"] is None
                or (len(preview["options"]), len(preview["question"]))
                > (len(record["options"] or []), len(record["question"]))
            ):
                record["question"] = preview["question"]
                record["options"] = preview["options"]
                record["verification"] = "quoted-poll-preview"
    for record in records:
        if record["question"] is None:
            when = connection.execute(
                "SELECT ZMESSAGEDATE FROM ZWAMESSAGE WHERE Z_PK=?",
                (record["localRecordId"],),
            ).fetchone()[0]
            nearby = connection.execute(
                """SELECT ZTEXT FROM ZWAMESSAGE
                   WHERE ZCHATSESSION=? AND ZTEXT IS NOT NULL
                     AND ABS(ZMESSAGEDATE-?)<=300
                     AND (LOWER(ZTEXT) LIKE '%question of the day%'
                       OR LOWER(ZTEXT) LIKE '%question of the night%')
                   ORDER BY ABS(ZMESSAGEDATE-?) LIMIT 1""",
                (chats[0][0], when, when),
            ).fetchone()
            if nearby:
                record["nearbyQotdText"] = nearby[0]
                record["verification"] = "nearby-qotd-text-not-poll-title"
        title = record["question"] or record["nearbyQotdText"] or ""
        if re.search(r"question of the (day|night)", title, re.IGNORECASE):
            record["qotdMarker"] = "explicit"
    connection.close()
    options.output.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "candidatePollCount": len(records),
        "questionsFromQuotePreviews": sum(bool(r["question"]) for r in records),
        "nearbyQotdTextCandidates": sum(bool(r["nearbyQotdText"]) for r in records),
        "missingQuestionContext": sum(not r["question"] and not r["nearbyQotdText"] for r in records),
        "records": records,
    }
    options.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Candidate polls:", output["candidatePollCount"])
    print("Questions from quoted previews:", output["questionsFromQuotePreviews"])
    print("Nearby QOTD texts (not exact poll titles):", output["nearbyQotdTextCandidates"])
    print("No recovered question context:", output["missingQuestionContext"])
    print("Full options from quoted previews:", sum(bool(r["options"]) for r in records))
    print("Private catalog:", options.output)
    def table_text(s):
        return " ".join((s or "").split()).replace("|", r"\|")

    report = [
        "# WhatsApp poll inventory (private)",
        "",
        "Read-only survey of the EBS-Socializing group. These 38 are candidate poll messages, not 38 distinct QOTDs.",
        "",
        "A quoted preview supplies an original poll question. A nearby QOTD text message supplies context only, not a verified poll title. Empty values are unknown, not negative.",
        "",
        "| Local ID | Date (Berlin) | Question or nearby context | Choices in quote | Evidence |",
        "|---|---|---|---:|---|",
    ]
    for r in records:
        title = r["question"] or r["nearbyQotdText"] or "Not recovered"
        title = table_text(title)
        report.append(
            f"| {r['localRecordId']} | {r['localDateTime'][:10]} | "
            f"{title} | {len(r['options']) if r['options'] is not None else 'Unknown'} | "
            f"{r['verification']} |"
        )
    report += [
        "",
        "The detailed option lists are in the adjacent poll_catalog.json file.",
        "Individual voters, names, phone numbers and raw chat history are not part of this inventory.",
    ]
    options.summary.parent.mkdir(parents=True, exist_ok=True)
    options.summary.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("Private summary:", options.summary)


if __name__ == "__main__":
    main()
