---
description: Search current jobs in Berlin or anywhere in Germany and get a scored shortlist
argument-hint: "<role> [in <city>] [remote] [english only] [new only]"
---

Use the berlin-job-search skill (`skills/berlin-job-search/SKILL.md`), "Search workflow".

- Parse the request: role, city (empty = Germany-wide), remote, English-only, only new since last time, time window (default 14 days).
- Read `job-search/profile.yml` if it exists and apply its preferences and dealbreakers. Don't block on a missing profile.
- Search with both the German and the English job title, each as its own query, choosing sources for the field (SKILL.md "Pick sources for the field"): product/business roles use `--sources ba,arbeitnow,ats,linkedin --title-match`, and other non-tech roles use `--sources ba,arbeitnow,linkedin --title-match`. For students, search Werkstudent roles and post-graduation roles separately. Use `--seen-file job-search/seen.json` and save results under `job-search/searches/`.
- Drop results whose title isn't the target role, and say how many you dropped. Quick-score the rest (`references/evaluating-jobs.md`), fetch details for the top ~10, and show a shortlist table: score, job (link), company, city, remote, German required with evidence, salary or "not stated", and why it fits. Save it to `job-search/shortlists/` and log the run in `job-search/progress.md`.
- End with ready-made LinkedIn/StepStone/Indeed/XING links for the same search and the next-step options (evaluate one, apply, track).

Request: $ARGUMENTS
