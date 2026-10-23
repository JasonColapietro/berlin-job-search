---
# generated from commands/upskill.md, do not edit.
description: Find the skills, certificates or language level holding you back, ranked from your target jobs, with a learning plan
argument-hint: "[optional: one job URL to analyse, or a target role]"
---

Use the berlin-job-search skill, "Gap analysis" section.

- With a job URL: fetch it (`scripts/job_detail.py`), compare it against `job-search/cv.md`, and list the gaps (blocker vs nice-to-have).
- Without one: collect the gaps from `job-search/reports/*.md` and the top-scored jobs in recent `job-search/searches/*.json`, then rank them by how often they appear, weighted by job score.
- Give a short learning plan for the top 3–5 gaps, including Germany-specific options where relevant: German courses (BAMF integration course, Volkshochschule, Goethe/telc exams), Bildungsgutschein via the Agentur für Arbeit, and recognition of foreign degrees (see `references/unemployment-and-support.md` and `references/visa-and-work-permits.md`).

Input (optional): $ARGUMENTS
