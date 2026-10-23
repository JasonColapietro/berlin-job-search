# Contributing

Thanks for helping make Germany-specific job searching more useful and trustworthy.

## Setup and checks

The core skill scripts use only the Python standard library; no install is needed to use or test them. Run:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_skill.py
```

The ChatGPT MCP server tests need Python 3.12 and the optional server dependencies:

```bash
python3 -m pip install -r chatgpt/server/requirements.txt
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

## Claude.ai upload compatibility

Anthropic's [Claude Help skill-creation guide](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) documents a ZIP whose root is the named skill directory and says the frontmatter description is limited to 200 characters. The [Claude Skills authoring guide](https://claude.com/docs/skills/how-to) currently says descriptions may be up to 1,024 characters, so the official docs disagree. The canonical skill description is 853 characters; the ChatGPT skill description is 873 characters. Do not describe the current ZIP as verified for Claude.ai until Anthropic clarifies or those descriptions are shortened.

Anthropic Help lists Free, Pro, Max, Team and Enterprise with code execution enabled. Its [network access guide](https://support.anthropic.com/en/articles/12111783-create-and-edit-files-with-claude) says network access is available for approved sources on Free/Pro/Max, while Team and Enterprise administrators control it (disabled by default). This does not guarantee access to every public job API. The skill Help page says uploads are subject to size limits but does not publish a Skills-specific numeric ZIP limit; the general file-creation guide lists 30 MB per file. The required folder-at-ZIP-root structure is implemented by `tools/package_skill.py`.
