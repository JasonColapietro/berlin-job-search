# Third-party notices

## career-ops

This project adapts German-market language, negotiation, interview-story and application-safety concepts from [career-ops](https://github.com/santifer/career-ops), especially [`modes/de/_shared.md`](https://raw.githubusercontent.com/santifer/career-ops/main/modes/de/_shared.md) and [`modes/de/angebot.md`](https://raw.githubusercontent.com/santifer/career-ops/main/modes/de/angebot.md), © 2026 Santiago Fernández de Valderrama, MIT License.

Adapted portions appear in:

- `skills/berlin-job-search/references/glossary.md` — German employment-market terminology
- `skills/berlin-job-search/references/salary-and-compensation.md` — negotiation scripts
- `skills/berlin-job-search/references/applications-germany.md` — application guardrails
- `skills/berlin-job-search/references/interviews-and-offers.md` — STAR+R story framework and contract-terms guidance

The material is rewritten in English and generalized beyond AI roles.

```text
MIT License

Copyright (c) 2026 Santiago Fernández de Valderrama

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## job-client / Daily Berlin Jobs

ATS endpoint patterns, public-board parsing, the LinkedIn guest parser and the starter company catalog in `skills/berlin-job-search/scripts/search.py`, `skills/berlin-job-search/scripts/linkedin.py` and `skills/berlin-job-search/assets/companies.json` are informed by [job-client / Daily Berlin Jobs](https://github.com/umutyesildal/daily-berlin-jobs), © 2026 Umut Yesildal, MIT License. This project reimplements the interfaces with the standard library; it includes neither the original project nor private configuration.

```text
MIT License

Copyright (c) 2026 Umut Yesildal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## ai-job-search

LinkedIn guest-card/detail parsing and request mapping, Freehire query mapping and first-seen state adapt [ai-job-search](https://github.com/ai-job-search-dev/ai-job-search), especially `.agents/skills/linkedin-search/cli/src/`, `.agents/skills/freehire-search/cli/src/` and the `/rank` workflow in `tools/rank_state.py` / `.claude/commands/rank.md`. The drafter–reviewer gate, mock-interview roleplay and outcome/follow-up tracker adapt product concepts; the posting-integrity gate independently reimplements `/apply` and `tools/posting_guard.py`. No code is copied from those implementations. The source repository identifies © 2026 Mads Lorentzen and uses the MIT License. This skill's scripts use the standard library and omit login, cookies and authenticated workflows.

Adapted documentation appears in:

- `skills/berlin-job-search/references/api-sources.md`
- `skills/berlin-job-search/references/browser-search.md`
- `skills/berlin-job-search/references/job-sources.md`
- `skills/berlin-job-search/references/application-review.md`
- `skills/berlin-job-search/references/mock-interview.md`
- `skills/berlin-job-search/scripts/tracker.py`
- `skills/berlin-job-search/scripts/report.py`
- `tests/test_linkedin.py`
- `tests/test_search.py`

```text
MIT License

Copyright (c) 2026 Mads Lorentzen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
