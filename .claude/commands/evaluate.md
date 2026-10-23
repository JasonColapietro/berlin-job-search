---
# generated from commands/evaluate.md, do not edit.
description: Check one job posting against your profile (German requirement, visa salary, fit score 1-5, A-F report)
argument-hint: "<job URL, BA reference number, or pasted job text>"
---

Use the berlin-job-search skill (`skills/berlin-job-search/SKILL.md`), "Evaluate workflow".

1. Get the posting with `scripts/job_detail.py`, or `scripts/analyze_jd.py -` for pasted text. If the page needs a login (for example LinkedIn), ask the user to paste the text.
2. Report the integrity check first if it flags anything.
3. Run the full evaluation from `references/evaluating-jobs.md` (hard gates, blocks A–F, score and decision), quoting `job-search/cv.md` for every match. If there is no CV yet, score only what can be judged and say what is missing.
4. Save the report to `job-search/reports/` and add or update the tracker row with the score.

Posting: $ARGUMENTS
