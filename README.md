# Question of the Day in EBS

A simple, searchable public archive of Questions of the Day and aggregated WhatsApp poll results.

**Website:** https://the-aries.github.io/question-of-the-day-in-ebs/

**Add a new question:** [Use the simple submission form](https://the-aries.github.io/question-of-the-day-in-ebs/add.html) (or the [original GitHub form](https://github.com/The-Aries/question-of-the-day-in-ebs/issues/new?template=qotd.yml)).

## Add a question (no coding required)

1. Open **Add a question** on the website. Enter the original question and date.
2. Add a row for each answer choice, with a separate field for its vote count. Use **+ Add option** to add rows. Leave the vote field empty if unknown. For a text-only question, leave all options empty.
3. Choose whether the poll allowed multiple answers and whether it was anonymous; both default to **No**. Select **Continue on GitHub**. The question, choices, votes and Yes/No selections are filled in. Check the result and submit. The GitHub bot then prepares a **pull request** containing one small JSON file.
4. A maintainer checks the information and merges the PR. The website then updates automatically.

WhatsApp polls split by the original app's option limit belong to one logical question on this website. Combine their answer choices before submitting.

**No Git, code editor, CSV, Excel or Google account is necessary for contributors.** A free GitHub account is required at the final review/submit step. The original GitHub form remains available as a fallback.

See [CONTRIBUTING.md](CONTRIBUTING.md) for examples and review guidance.

## How it works

```text
GitHub Issue Form -> validation -> one JSON file + PR
                                    |
                            maintainer reviews
                                    |
                                merge to main
                                    |
                       GitHub Actions validates and builds
                                    |
                        GitHub Pages displays new data
```

- Source of truth: `entries/*.json` (one entry per logical question).
- Each logical question is stored as one main record. WhatsApp polls split by the option limit are combined in the source record, with original source poll details retained in `sourcePolls` for auditing.
- The builder (`scripts/build_archive.py`) groups related entries and generates `data/qotd.json`. This JSON is a **build artifact**, not the source of truth.
- Each question opens as a collapsed card. Users can search, filter by voting mode/date, use the side navigation list and view aggregate votes. Each card has one **Request to edit** link; its form also offers **Request deletion instead of editing**. Both generate PRs for review.
- A single-choice poll with complete counts can infer its participant count as the total of the choice counts. Multi-choice polls never infer unique participants from vote totals. Unknown numbers stay unknown.

## Preview locally

```bash
python3 scripts/build_archive.py
python3 -m http.server 8000
```

Open http://localhost:8000/. Run tests with:

```bash
python3 -m unittest discover -s tests -v
node --check app.js
node --check add.js
```

## Maintainer setup

This repository includes GitHub Actions for new-question and edit/delete PRs, validation and GitHub Pages deployment.

The automated PR feature requires repository Settings -> Actions -> General -> **Allow GitHub Actions to create and approve pull requests**. The workflow itself has scoped `contents: write`, `pull-requests: write` and `issues: write` permissions.

For GitHub Pages use Settings -> Pages -> **Source: GitHub Actions**. The deploy workflow publishes only the site HTML, JavaScript and validated JSON (not `entries/`, `private/` or working screenshots).

The QOTD Issue Form has a label `qotd-submission` to route submitted issues to the PR workflow. Bot-created PR checks may need a maintainer to approve the initial workflow run, according to GitHub's security controls.

Do not merge unreviewed submissions. Do not post WhatsApp raw exports, screenshots containing names, participant lists, phone numbers or individual ballots.

## Historical data coverage

The initial review identified 38 candidate poll messages in the EBS-Socializing chat. All 38 were reconstructed locally, but **eight do not have confirmed QOTD status**. Twenty-seven QOTD poll topics (including three original WhatsApp follow-up/continuation messages) and one text-only QOTD yield **28 logical questions**. The excluded candidates remain in the local private review.

Privacy-sensitive local inventory and screenshot evidence stay in `private/`, which Git ignores. Any uncertainty in the source is shown as unknown rather than fabricated.
