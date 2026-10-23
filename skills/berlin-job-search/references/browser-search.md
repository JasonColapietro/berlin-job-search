# Browser-driven job search recipes

These are recipes for an agent operating a real browser with the human present (for example Claude in Chrome, Playwright MCP, or a computer-use tool). Prefer official employer pages. Search-result URLs may change; confirm each filter in the live interface before relying on it.

## LinkedIn Jobs URL parameters

Base: `https://www.linkedin.com/jobs/search/`

| Parameter | Example | Meaning / confidence |
|---|---|---|
| `keywords` | `keywords=software%20engineer` | Search terms; widely used by the public jobs page. |
| `location` | `location=Berlin%2C%20Germany` | Display location text. |
| `geoId` | `101282230` Germany; `103035651` Berlin; `100495942` Munich; `101949806` Hamburg; `90009714` Frankfurt/Rhine-Main; `90009713` Cologne/Bonn | Each ID is checked by a guest search and a matching result-card location. A geoId is a region/metro, not always a city boundary. |
| `f_TPR` | `r86400`, `r604800`, `r1209600`, `r2592000` | Seconds in past 1, 7, 14, 30 days. The 7-day form returned cards; other values `(verify)` individually. |
| `f_WT` | `f_WT=1`, `2`, `3` | 1 on-site, 2 remote, 3 hybrid. The `3` form returned cards; verify exact labels against current UI filters. |
| `f_E` | `f_E=1,2,3,4,5,6` | 1 internship, 2 entry, 3 associate, 4 mid-senior, 5 director, 6 executive. Individual labels `(verify)` in current UI. |
| `f_JT` | `f_JT=F,P,C,T,I` | F full-time, P part-time, C contract, T temporary, I internship. Individual labels `(verify)` in current UI. |
| `f_AL` | `f_AL=true` | Easy Apply filter; a combined guest-endpoint request returned cards, but filter behavior is `(verify)` in a logged-in UI. |
| `sortBy` | `sortBy=DD` | Date sort; accepted in the live guest-endpoint request, ordering `(verify)` in the UI. |
| `start` | Guest endpoint: `start=0`, `10`, `20`; logged-in web UI uses 25-card pages `(verify)`. | Guest endpoint is zero-based, 10 cards per page; web UI pagination differs. |

Example: `https://www.linkedin.com/jobs/search/?keywords=data%20analyst&location=Berlin%2C%20Germany&geoId=103035651&f_TPR=r604800&sortBy=DD`. Use the logged-in browser only if the user chooses to sign in; never ask for passwords or handle authentication. Search-card and detail parameters for the low-volume guest source are documented in [API sources](api-sources.md).

## XING Jobs

Open [XING Jobs](https://www.xing.com/jobs) and use its own search controls for title, city, workplace model, and salary. A live URL with `keywords=software engineer&location=Berlin` redirected to the `/jobs/search/ki` route and retained those query values. Radius and filter parameter names/identifiers are `(verify)`; XING's current help recommends searching inside Jobs and managing preferences in the profile. See [Find your new job with XING](https://help.xing.com/hc/en-us/articles/31499161470237-Find-your-new-job-with-XING).

## StepStone

Search at [StepStone](https://www.stepstone.de/). A current path pattern commonly appears as `/jobs/{role}/in-{city}`; radius and freshness options are UI filters and their stable URL keys are `(verify)`. A template like `/jobs/software-engineer/in-berlin?radius=25` is illustrative, not a guaranteed working filter. Confirm the city, radius, and date chips in the page before extracting.

## Indeed Germany

Base: `https://de.indeed.com/jobs/`

| Parameter | Example | Meaning |
|---|---|---|
| `q` | `q=Pflegefachkraft` | Query |
| `l` | `l=Hamburg` | Location |
| `radius` | `radius=25` | Search radius in km |
| `fromage` | `fromage=7` | Days since posting |

Example: `https://de.indeed.com/jobs?q=Pflegefachkraft&l=Hamburg&radius=25&fromage=7`. These query keys are widely used; an automated check returned HTTP 403, so their current behavior is `(verify)` in a human browser. Indeed may normalize or discard them on redirect; confirm active filters.

## Bundesagentur für Arbeit

Open [BA Jobsuche](https://www.arbeitsagentur.de/jobsuche/), enter the role and city, then refine date, radius, and job type in the web UI. A commonly used path shape is `/jobsuche/suche?was=...&wo=...`; the stable current browser parameter names beyond those are `(verify)`. The script API is documented separately in [API sources](api-sources.md).

## Hiring.cafe

The service redirects `hiring.cafe` to [hiringcafe.com](https://hiringcafe.com/). In the 2026-10-23 check, both curl and a real Playwright Chromium page reached a Cloudflare verification challenge (HTTP 403, page title “Just a moment…”). No search UI or job API request was observed. Do not automate or solve the verification challenge; ask the user to open the site in their normal browser and continue manually if needed.

When the human has access:

1. Enter a role such as “software engineer” and location “Berlin”; inspect the site's own visible filters and result cards. Hiring.cafe describes itself as an aggregator of ATS postings with salary, seniority, and language filters, but the current controls and field names are `(verify)` because the live UI was blocked.
2. Confirm a role on the employer's ATS page. Do not use the old unauthenticated scraper API: the checked `GET /api/search-jobs` returned 401, `POST /api/search-jobs` returned 405, and `/api/search-jobs/get-total-count` returned 404.
3. If the page becomes available, run a small in-page extraction over result cards only. The generic selectors below are a starting point; actual field selectors and `data-testid` names are **(verify)** against the live DOM:

```js
(() => {
  const text = (node) => node?.textContent?.replace(/\s+/g, " ").trim() || null;
  return [...document.querySelectorAll('a[href*="/job"], a[href*="/jobs"]')]
    .map((link) => {
      const card = link.closest('article, li, [data-job-id], [class*="job-card"]') || link.parentElement;
      const field = (name) => card?.querySelector(`[data-testid="${name}"]`);
      return {
        title: text(field("job-title")) || text(link),
        company: text(field("company")),
        location: text(field("location")),
        salary: text(field("salary")),
        seniority: text(field("seniority")),
        language: text(field("language")),
        url: new URL(link.getAttribute("href"), location.href).href
      };
    })
    .filter((job) => job.title && job.url);
})();
```

Keep the result set small. Never use `get_page_text` on the whole results page; extract the fields from a handful of cards and read a chosen detail page only after user selection. If the UI exposes an in-page JSON fetch after a human search, use it only in that page context and only after confirming its response shape; API details remain `(verify)`.

## Extraction and pacing

- Extract only structured result-card fields: title, employer, location, date, remote/hybrid label, and canonical job URL. Prefer DOM attributes, JSON-LD, or accessible text of one card.
- Never dump the whole page text into model context. Select a small number of relevant cards and fetch only a chosen detail page.
- Wait 2–4 seconds between page loads; use no more than three pages per query and inspect no more than 25 cards per page.
- Treat cookie notices, login screens, CAPTCHA, 2FA, and access-denied pages as a stop. Hand control to the user; do not evade or solve them.
- A browser may show personalized or stale recommendations. Confirm job state and requirements on the employer's own page.

### Small-card extraction example

Use a browser evaluator only after the page is accessible. Adjust selectors to the page's current markup; return at most the visible cards and never the page body:

```js
(() => {
  const text = (node) => node?.textContent?.replace(/\s+/g, " ").trim() || null;
  return [...document.querySelectorAll("li.base-search-card")]
    .slice(0, 25)
    .map((card) => {
      const link = card.querySelector("a.base-card__full-link");
      return {
        title: text(card.querySelector("h3.base-search-card__title")),
        company: text(card.querySelector("h4.base-search-card__subtitle")),
        location: text(card.querySelector(".job-search-card__location")),
        date: card.querySelector("time")?.getAttribute("datetime") || null,
        url: link ? new URL(link.getAttribute("href"), location.href).href.split("?")[0] : null
      };
    })
    .filter((card) => card.title && card.url);
})();
```

This LinkedIn selector set was verified against the public guest card markup. It may change; if fields stop appearing, capture one selected card's DOM and revise the extractor rather than falling back to the full page. Other boards need their own small selectors and a human page check.

### Search-session checklist

1. Confirm the chosen source, role keywords, city, radius, date, and work-model filters before loading results.
2. Record the exact URL or visible filter chips so the user can reproduce the query.
3. Inspect card titles and locations first; only open details for a small, relevant shortlist.
4. Confirm freshness and application destination on the employer's own careers page.
5. Keep profile, login, and saved-job actions in the user's hands.

For LinkedIn, the public guest endpoint can be useful for a low-volume discovery pass, but the [User Agreement](https://www.linkedin.com/legal/user-agreement) prohibits unauthorized automated access. Use the direct CLI only with its warning and hard cap; a normal browser search remains the safer choice. If access is challenged, stop.

## Approval boundaries

Never click **Apply**, **Submit**, **Send**, or equivalent. Never send recruiter messages, connection requests, or referrals without explicit per-item user approval. No bulk messaging. Saving a job, setting an alert, changing a profile, or sharing a CV also requires explicit confirmation. The user reviews any drafted text and performs the action.

If an application flow starts automatically from a listing, stop before submitting data and return control. Do not upload a CV or enter work authorization, salary, or demographic information on the user's behalf.

## Result review worksheet

For a small shortlist, capture only the fields needed to compare postings:

| Field | Record |
|---|---|
| Job title and employer | Exact visible title and legal/brand name if shown |
| City / work model | City, on-site/hybrid/remote label, allowed work country |
| Freshness | Structured date or the site's visible age label |
| Language | Explicit German/English requirement or “not stated” |
| Salary | Posted range and pay period; do not infer missing figures |
| Contract | Full-time/part-time/fixed-term/other if visible |
| URL | Canonical posting URL, not a search-result tracking URL |
| Next step | “Review”, “ask user”, or “verify employer page”; never “apply” by default |

If a card does not expose a field, record `unknown` rather than extracting the entire page or guessing from the employer's reputation.
