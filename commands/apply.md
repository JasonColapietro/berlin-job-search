---
description: Write a tailored German Lebenslauf/Anschreiben or English CV/cover letter for one job, reviewed and rendered to PDF
argument-hint: "<job URL, tracker id, or company + role>"
---

Use the berlin-job-search skill (`skills/berlin-job-search/SKILL.md`), "Apply workflow", and follow `references/application-review.md` exactly:

1. Make sure the job has been evaluated (run the evaluation first if not) and save the posting text.
2. Writer pass from `job-search/cv.md` only, using the templates in `assets/`. Pick German or English format per the reference.
3. An independent reviewer pass against R1–R9 with `scripts/ats_check.py`, and at most two revision rounds. If facts are missing, ask; never write around them.
4. Render with `scripts/render_doc.py` to PDF (or print-ready HTML).
5. Hand-off: file paths, the claims diff, the reviewer table, and drafted form answers. The user submits it themselves.
6. After the user confirms they applied: `scripts/tracker.py archive … --fetch-posting`, then `event <id> applied`.

Job: $ARGUMENTS
