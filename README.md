# QOTD Archive

A small, searchable static Question of the Day archive.

Live page: https://the-aries.github.io/qotd-archive/

## Local preview

From the repository root, run: python3 -m http.server 8000

Open: http://localhost:8000/

## Updating questions

Edit data/qotd.json. Keep dates in Europe/Berlin local time. Publish only verified questions, answer choices and aggregated results. Unverified vote counts remain null, never zero.
Open-ended QOTDs without poll options are also in scope; represent them with an empty options array. Do not assume that only the repository owner's posts qualify.

For a local, read-only inventory on a Mac with WhatsApp installed, run:

    python3 scripts/scan_polls.py --chat "EBS-Socializing"

The group-wide inventory, including polls authored by other group members and text messages mentioning QOTD, is written under private/ and excluded from Git. WhatsApp poll message type 46 was observed in this installation in November 2026; it is not a documented public API. This count is **all group polls**, not necessarily QOTDs, and text-only QOTDs can also exist.

## Data protection

Do not commit group messages, participant identities, phone numbers, raw chat exports or database records. Poll-message count is not necessarily the number of unique QOTDs; split and unrelated polls require manual review.
