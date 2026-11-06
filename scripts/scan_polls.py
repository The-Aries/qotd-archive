#!/usr/bin/env python3
"""List potential WhatsApp poll records without modifying a live database."""
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
        """SELECT m.Z_PK, m.ZMESSAGEDATE
           FROM ZWAMESSAGE m
           WHERE m.ZCHATSESSION = ? AND m.ZISFROMME = 1 AND m.ZMESSAGETYPE = 46
           ORDER BY m.ZMESSAGEDATE DESC""",
        (chats[0][0],),
    ).fetchall()
    con.close()
    tz = ZoneInfo("Europe/Berlin")
    records = [
        {
            "localDateTime": (EPOCH + timedelta(seconds=t)).astimezone(tz).isoformat(timespec="seconds"),
            "localRecordId": key,
            "reviewStatus": "unverified"
        }
        for key, t in rows
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"candidatePollCount": len(records), "records": records}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Candidate poll messages authored by this account:", len(records))
    print("Distinct calendar dates:", len(set(r["localDateTime"][:10] for r in records)))
    print("Private inventory:", args.output)
    print("Not a verified count of distinct Questions of the Day.")


if __name__ == "__main__":
    main()
