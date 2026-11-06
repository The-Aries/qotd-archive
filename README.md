# QOTD Archive

A small, searchable static Question of the Day archive.

Live page: https://the-aries.github.io/qotd-archive/

## Local preview

From the repository root, run: python3 -m http.server 8000

Open: http://localhost:8000/

## Updating questions

Edit data/qotd.json. Keep dates in Europe/Berlin local time. Publish only verified questions, answer choices and aggregated results. Unverified vote counts remain null, never zero.

For a local, read-only inventory on a Mac with WhatsApp installed, run:

    python3 scripts/scan_polls.py --chat "EBS-Socializing"

The inventory is written under private/ and is excluded from Git. WhatsApp poll message type 46 was observed in this installation in November 2026; it is not a documented public API.

## Data protection

Do not commit group messages, participant identities, phone numbers, raw chat exports or database records. Poll-message count is not necessarily the number of unique QOTDs; split and unrelated polls require manual review.
