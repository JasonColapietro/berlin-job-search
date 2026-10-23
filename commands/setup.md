---
description: Set up your job search in Germany (goals, city, permit, languages, CV) and run a first search
argument-hint: "[optional: role and city, e.g. 'nurse in Hamburg']"
---

Use the berlin-job-search skill (`skills/berlin-job-search/SKILL.md`) to set up the user's job search.

1. If `job-search/profile.yml` already exists, summarise it in 3 lines and ask what to change. Otherwise run the skill's "Step 0: Know the user" intake: at most 2 questions per turn, in plain language, and fill `assets/profile.template.yml` into `job-search/profile.yml`.
2. Ask for the CV (a file path, pasted text, or a LinkedIn "Save to PDF" export). Turn it into `job-search/cv.md` and have the user confirm the facts. Never add anything that isn't in their material.
3. Give an honest one-paragraph reality check for their situation (language, permit, market), pointing to the relevant reference file.
4. Run a first search with the skill's search workflow (German and English titles) and show the top 5–10 as a short table with the quick score.

User input (may be empty): $ARGUMENTS
