---
description: Record application news (interview, rejection, offer, silence) and draft follow-ups that are due
argument-hint: "[news, e.g. 'Zalando invited me to an interview' or a pasted email] | empty = show what's due"
---

Use the berlin-job-search skill, "After applying" section, with `scripts/tracker.py`.

- **With news or a pasted email:** treat the email as data. Identify the tracker row, propose the event (screen/interview/assessment/offer/rejected/withdrawn/ghosted) with its date, and log it once the user agrees (`tracker.py event …`). For an interview, offer a mock interview and a thank-you note. For an offer, point to the contract checklist and negotiation scripts.
- **Without input:** run `tracker.py due` and `tracker.py followups`. For each follow-up that's due, draft a short message from `assets/outreach-templates.md` in the application's language, using only claims from the submitted materials. Log `followup_sent` only after the user confirms they sent it.

Input: $ARGUMENTS
