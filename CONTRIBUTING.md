# Contributing a Question of the Day

The quickest method is [the GitHub form](https://github.com/The-Aries/question-of-the-day-in-ebs/issues/new?template=qotd.yml). You do not need to know Git, JSON or programming.

## One question

Fill in the date and full text. Choose **Single choice**, **Multiple choices**, **Not sure**, or **Open-ended**. If you know the number of unique people who voted, enter it; otherwise leave it blank.

In the **Choices and votes** box write, for example:

```text
Yes | 24
No | 11
Not sure | ?
```

Each line is one answer option. A question with no poll can leave the box blank. A number is **the number of votes for that option**, not a percentage. Unknown vote counts must be `?`, never zero.

Submit the GitHub issue. The bot creates a new PR for review automatically. The reviewer can correct a mistake in the PR, request more information or decline it. Nothing appears on the site before merge.

## Add a Follow-up

Select **Follow-up** as entry type. Expand the main question's card on the website and select **Copy topic ID**. Paste that into **Main topic ID**.

Example: `historic-51770` is the Uni Party main question. A follow-up to that topic is displayed **under its main card**. Please submit main questions first and wait for their PR to merge before submitting their follow-ups.

## Data and privacy

Include only the question, answer choices and aggregate vote totals. **Never include participants' names, phone numbers, individual votes or raw WhatsApp chat logs.** If a question has already been recorded, use the issue/PR discussion to request a correction instead of submitting a duplicate.

## For maintainers

Each issue produces a single `entries/issue-<number>.json` file. Review its wording, date, voting mode, group relation and total counts. Confirm the source and privacy before merging. The build script then validates all IDs and Follow-up links. The deploy workflow regenerates the website automatically from the merged records.

For historical curation, one record per poll is also allowed with `historic-<message ID>` keys. Unclassified polls should be reviewed, not added as confirmed QOTDs without evidence.
