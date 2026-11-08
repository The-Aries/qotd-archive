# Contributing a Question of the Day

The quickest method is [the simple website form](https://the-aries.github.io/question-of-the-day-in-ebs/add.html). Every option has separate text and vote-count fields; click **+ Add option** for more. Choose whether multiple answers were allowed and whether the original poll was anonymous (both default to **No**). This prepares the existing GitHub issue form with your selections filled in, which you review and submit. You do not need to know Git, JSON or programming.

## One question

Fill in the date and full text. Choose **Single choice**, **Multiple choices**, **Not sure**, or **Open-ended**. If you know the number of unique people who voted, enter it; otherwise leave it blank.

If you prefer the [original GitHub form](https://github.com/The-Aries/question-of-the-day-in-ebs/issues/new?template=qotd.yml), enter the choices in the **Choices and votes** box, for example:

```text
Yes | 24
No | 11
Not sure | ?
```

Each line is one answer option. A question with no poll can leave the box blank. A number is **the number of votes for that option**, not a percentage. Unknown vote counts must be `?`, never zero.

Submit the GitHub issue. The bot creates a new PR for review automatically. The reviewer can correct a mistake in the PR, request more information or decline it. Nothing appears on the site before merge.

## Report, edit, or delete an existing question

Expand a question on the website, then select **Report**, **Edit**, or **Delete**.
Reports create a GitHub issue for a maintainer. Edits open the website form with the original question, options and aggregate votes already filled in. Deletion requests open a GitHub form containing the matching question ID. Both edits and deletions generate **reviewable PRs**, never direct site changes. A stale edit or deletion is rejected if the question has already been changed.

WhatsApp polls that were split due to option-count limits are presented as **one logical question**. Enter their options as one list; do not submit separate Follow-ups.

## Data and privacy

Include only the question, answer choices and aggregate vote totals. **Never include participants' names, phone numbers, individual votes or raw WhatsApp chat logs.** If a question has already been recorded, use the issue/PR discussion to request a correction instead of submitting a duplicate.

## For maintainers

Each issue produces a single `entries/issue-<number>.json` file. Review its wording, date, voting mode, group relation and total counts. Confirm the source and privacy before merging. The build script then validates all IDs and Follow-up links. The deploy workflow regenerates the website automatically from the merged records.

For historical curation, one record per poll is also allowed with `historic-<message ID>` keys. Unclassified polls should be reviewed, not added as confirmed QOTDs without evidence.
