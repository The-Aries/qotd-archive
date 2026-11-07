#!/usr/bin/env python3
"""Inventory group-wide WhatsApp poll and text QOTD candidates, read-only."""
import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
DEFAULT_DB = Path.home() / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat", required=True, help="Unique substring of a WhatsApp group name")
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=Path("private/poll_inventory.json"))
    args = parser.parse_args()
    database = args.database.expanduser().resolve(strict=True)
    con = sqlite3.connect("file:" + quote(str(database), safe="/") + "?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    chats = con.execute(
        "SELECT Z_PK, ZPARTNERNAME FROM ZWACHATSESSION WHERE ZPARTNERNAME LIKE ?",
        ("%" + args.chat + "%",),
    ).fetchall()
    if len(chats) != 1:
        raise SystemExit(f"Expected one matching chat, found {len(chats)}. Use a more specific --chat.")
    rows = con.execute(
        """SELECT m.Z_PK, m.ZMESSAGEDATE, m.ZISFROMME
           FROM ZWAMESSAGE m
           WHERE m.ZCHATSESSION = ? AND m.ZMESSAGETYPE = 46
           ORDER BY m.ZMESSAGEDATE DESC""",
        (chats[0][0],),
    ).fetchall()
    text_rows = con.execute(
        """SELECT m.Z_PK, m.ZMESSAGEDATE, m.ZISFROMME
           FROM ZWAMESSAGE m
           WHERE m.ZCHATSESSION = ?
             AND (LOWER(m.ZTEXT) LIKE '%qotd%'
               OR LOWER(m.ZTEXT) LIKE '%question of the day%')
           ORDER BY m.ZMESSAGEDATE DESC""",
        (chats[0][0],),
    ).fetchall()
    con.close()
    tz = ZoneInfo("Europe/Berlin")
    def describe(rows):
        return [
        {
            "localDateTime": (EPOCH + timedelta(seconds=t)).astimezone(tz).isoformat(timespec="seconds"),
            "localRecordId": key,
            "isFromThisAccount": bool(own),
            "reviewStatus": "unverified"
        }
        for key, t, own in rows
        ]

    records = describe(rows)
    text_candidates = describe(text_rows)
    from_this_account = sum(r["isFromThisAccount"] for r in records)
    dates = len(set(r["localDateTime"][:10] for r in records))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({
            "candidatePollCount": len(records),
            "fromThisAccount": from_this_account,
            "fromOtherAccounts": len(records) - from_this_account,
            "distinctPollDates": dates,
            "keywordTextMessageCount": len(text_candidates),
            "pollRecords": records,
            "keywordTextRecords": text_candidates
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Group-wide candidate poll messages:", len(records))
    print("From this account:", from_this_account)
    print("From other accounts:", len(records) - from_this_account)
    print("Distinct calendar dates with polls:", dates)
    print("QOTD keyword text messages (may overlap with polls):", len(text_candidates))
    print("Private inventory:", args.output)
    print("Not a verified count of distinct Questions of the Day.")


if __name__ == "__main__":
    main()
