---
# generated from commands/report.md, do not edit.
description: Show how your job search is going - funnel, response rates, sources - and build the offline HTML dashboard
argument-hint: "[optional: focus, e.g. 'which sources work best']"
---

Use the berlin-job-search skill with `scripts/tracker.py stats` and `scripts/report.py`.

1. Run `tracker.py stats` and summarise it in plain language: applications, response rate, interviews, offers, and what is due.
2. Generate `job-search/report.html` with `report.py` and tell the user to open it in a browser.
3. If 10 or more applications have resolved, compare which sources, roles and document formats got responses, and suggest one or two concrete changes (search terms, cities, CV emphasis, quick-score weights).

Focus (optional): $ARGUMENTS
