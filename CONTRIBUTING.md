# Contributing

Thanks for helping make Germany-specific job searching more useful and trustworthy.

## Setup and checks

The core skill scripts use only the Python standard library. Run:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_skill.py
```

## Add a company board

Add a fictional or public company entry to `skills/berlin-job-search/assets/companies.json`. Use the conventions of nearby entries:

- `name`: company display name.
- `ats`: one of `greenhouse`, `lever`, `ashby`, `personio`, `smartrecruiters`, `recruitee`, `workable` or `join`.
- `slug`: the public board/account identifier used by that ATS. Find it in the employer's public career-page URL or board API, then verify the endpoint format against the source documentation.
- `career_page`: the employer's public careers page.
- `city`: the main city when the company entry is location-specific.

Only add public boards that can be fetched without a login or credential. Before submitting the change, run a targeted live search from your own machine and confirm the board fetch returns at least one job. Do not put live requests in tests or CI.

## Add a job source

Prefer unauthenticated public APIs with documented terms and stable response formats. Keep implementations dependency-free and polite: use bounded requests, respect pagination and rate limits, and return partial errors rather than discarding successful results. Add parser tests with fictional fixtures, document the source URL and the date you verified its behavior, and never add personal CVs or application records to fixtures, issues or pull requests.

## Pull requests

Keep changes focused, include offline tests, run the validator, and explain any live-only manual checks. Do not include personal job-search data.
