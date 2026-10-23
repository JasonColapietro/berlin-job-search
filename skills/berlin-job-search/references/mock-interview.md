# Mock interview mode

A realistic practice interview for one specific application, in German or English, followed by
honest feedback. Use it when the user says "practice", "mock interview", "Probeinterview", or has
an interview coming up.

## 1. Set up (ask in one message, with defaults)

| Setting | Options | Default |
|---|---|---|
| Job | A tracker id, report, or pasted posting | The most recent tracker row with status `interview` |
| Stage | HR screen (*Erstgespräch*), hiring manager (*Fachgespräch*), technical, case / take-home debrief, final / culture (*Zweitgespräch*) | The next stage per the tracker events |
| Language | German, English, or mixed (common in Berlin: HR in German, team in English) | The posting's language |
| Length | 5, 8 or 12 questions | 8 |
| Interviewer style | Friendly, neutral, or tough (more follow-ups and pushback) | Neutral |
| Feedback timing | At the end (realistic) or after each answer (coaching) | At the end |

Before starting, read `cv.md`, the posting (`applications/<folder>/posting.md` if archived), the
evaluation report (block F stories and gaps), and any earlier mock or interview notes in
`job-search/interview-prep/`. If the user is non-EU, expect a work-permit question. Let the user
practice the answer they prepared from `references/visa-and-work-permits.md`.

## 2. Run the interview

- **Play the interviewer.** Introduce yourself with a plausible role (for example "Anna,
  Talent Acquisition" or "Tobias, Engineering Lead"). Use only company facts from the posting or
  the company's own public pages. Don't invent internal details.
- **One question at a time.** Wait for the answer. Never answer for the user.
- **Follow up like a real interviewer** (1–2 probes when an answer is vague): "What was *your*
  part?", "What was the result in numbers?", "What would you do differently?", "Wie sind Sie
  konkret vorgegangen?"
- **Stay in character** until the end, unless the user types `pause`, `hint`, or `stop`.
  - `hint`: a one-line nudge (which story or requirement fits), then continue in character.
  - `pause`: step out, answer the user's question, resume on request.
  - `stop`: go straight to feedback.
- **Mix of questions per stage:**

| Stage | Typical questions |
|---|---|
| HR screen | Walk me through your CV. Why this company? Why are you leaving or did you leave? *Gehaltsvorstellung?* *Kündigungsfrist / frühestmöglicher Eintritt?* Work permit / relocation? Language levels (they may switch language mid-call to test). |
| Hiring manager | Behavioural questions mapped to the posting's top 3 requirements; a conflict or failure story; prioritisation; "Stärken und Schwächen"; "Wo sehen Sie sich in fünf Jahren?" |
| Technical | Role-specific depth questions drawn from the posting's tech stack and the user's CV claims (probe what the CV says they did); a short system-design or problem-solving prompt described in words; trade-off questions. Don't run live coding unless asked. |
| Case / take-home debrief | "Walk us through your solution", "Why this approach?", "What would you change with more time?" |
| Final / culture | Team fit, working style (remote/hybrid expectations), questions for us, motivation for Germany/Berlin if relocating. |

- **German-specific realism:**
  - Formal *Sie* unless the interviewer offers *du* (many Berlin startups do; follow the user's setting).
  - Expect direct questions about salary and notice period early on.
  - Questions about gaps in the CV (*Lücken im Lebenslauf*) are common. Practise a calm, factual answer.
  - Questions about marital status, family plans, religion, pregnancy or health are **not
    permitted** under the AGG. Include at most one such question per session, and only when the
    user asked for a tough interviewer, so they can practise declining politely. Explain it in the
    feedback.
- End in character: "Haben Sie noch Fragen an uns?" / "Do you have any questions for us?" Then
  respond briefly to the user's questions.

## 3. Feedback

Score each answer 1–5 on four dimensions and give one concrete fix:

| Dimension | 5 looks like |
|---|---|
| **Structure** | Clear STAR+R: situation and task in 1–2 sentences, mostly action, a concrete result, a short reflection |
| **Relevance** | Answers the actual question and links to a requirement in the posting |
| **Evidence** | Specific, personal ("I"), with numbers or outcomes that match `cv.md` |
| **Delivery** | 60–120 seconds when spoken (about 150–300 words), confident, right register and language level |

Then give:
1. **Overall readiness** for this stage: ready / almost / not yet, with one sentence why.
2. **Top 3 improvements**, ranked by impact.
3. **A rewritten stronger answer** for the 2 weakest questions, using **only facts the user said
   or that appear in `cv.md`**. Mark any placeholder where a fact is missing: `[result: ask user]`.
4. **Red flags** the interviewer would note (contradictions with the CV, salary anchored too low,
   negative talk about a former employer, an unclear permit status).
5. **Language notes** if the interview was in German or English as a second language: 3–5
   corrections and phrases worth memorising (a short list, not a lesson).

Be honest. Don't inflate scores. Encouragement comes from specific progress, not generic praise.

## 4. Save and log

Write `job-search/interview-prep/<tracker-id>-mock-<YYYY-MM-DD>.md` with the settings, questions,
the user's answers (summarised), scores, and the improvements. Then:
```bash
python3 "$SKILL_DIR/scripts/tracker.py" event <id> note --note "mock interview (<stage>): <readiness>"
```
Before the real interview, offer a short second round focused on the weakest answers.
After the real interview, offer a thank-you note (`assets/outreach-templates.md`) and log it with
`tracker.py event <id> interview` (and `thank_you_sent` once the user has sent the note).
