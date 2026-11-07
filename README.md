# Question of the Day Archive

A simple, searchable public archive of Questions of the Day and aggregated WhatsApp poll results.

**Website:** https://the-aries.github.io/qotd-archive/

**Add a new question:** [Fill in the GitHub form](https://github.com/The-Aries/qotd-archive/issues/new?template=qotd.yml)

## Add a question (no coding required)

1. Open **Add a new question** and fill in the original question, date, voting mode and answer choices.
2. Enter each choice on its own line as `Choice | number`. Use `?` if the vote count is unknown. For an open-ended question, leave the choices blank.
3. Submit the form. The GitHub bot creates a **pull request** containing one small JSON file.
4. A maintainer checks the information and merges the PR. The website then updates automatically.

Follow-up questions: choose **Follow-up** in the form, and paste the parent topic ID (for example `historic-51770` or `issue-123`). Follow-ups are shown inside their main question's card, not as separate QOTDs.

**No Git, code editor, CSV, Excel or Google account is necessary for contributors.** A free GitHub account is required to submit the form.

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

- Source of truth: `entries/*.json` (one entry per original poll or text-only question).
- Main entries have `kind: "main"`; Follow-ups have `kind: "followup"` and a `parentId`.
- The builder (`scripts/build_archive.py`) groups related entries and generates `data/qotd.json`. This JSON is a **build artifact**, not the source of truth.
- Each question opens as a collapsed card. Users can search, filter by category/type/date and view each option's aggregated vote count.
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
```

## Maintainer setup

This repository includes three GitHub Actions: **QOTD form to pull request**, **Validate QOTD**, and **Deploy QOTD archive**.

The automated PR feature requires repository Settings -> Actions -> General -> **Allow GitHub Actions to create and approve pull requests**. The workflow itself has scoped `contents: write`, `pull-requests: write` and `issues: write` permissions.

For GitHub Pages use Settings -> Pages -> **Source: GitHub Actions**. The deploy workflow publishes only the site HTML, JavaScript and validated JSON (not `entries/`, `private/` or working screenshots).

The QOTD Issue Form has a label `qotd-submission` to route submitted issues to the PR workflow. Bot-created PR checks may need a maintainer to approve the initial workflow run, according to GitHub's security controls.

Do not merge unreviewed submissions. Do not post WhatsApp raw exports, screenshots containing names, participant lists, phone numbers or individual ballots.

## Historical data coverage

The initial review identified 38 candidate poll messages in the EBS-Socializing chat. All 38 were reconstructed locally, but **eight do not have confirmed QOTD status**. Only 27 confirmed QOTD poll groups, their three nested follow-up/continuation polls, and one standalone text-only QOTD were selected for the initial public archive. The excluded candidates remain in the local private review and are not silently counted as QOTDs.

Privacy-sensitive local inventory and screenshot evidence stay in `private/`, which Git ignores. Any uncertainty in the source is shown as unknown rather than fabricated.
