# The Polite Scraper — FlyRank A9

A small, polite scraping pipeline that downloads the first three catalogue pages of
[Books to Scrape](https://books.toscrape.com), visits all 60 book pages, turns messy
HTML into clean, validated JSON records, survives a broken page without crashing, and
ends every run with an honest report of what happened.

## Target classification

**Site:** books.toscrape.com

**Why this target is appropriate:** Books to Scrape is a public sandbox site built
specifically for people to practice web scraping on. It exists for exactly this kind
of exercise — no real business, personal data, or paywalled content is involved.

**Scope:** This scraper only touches the first 3 catalogue pages (60 books total). It
does not crawl the entire site.

**Data collected:** For each book — title, price, availability, star rating,
description, and the product page URL. All fields are already present in the HTML the
server sends; no login or hidden data is involved.

**robots.txt result:** Requested `https://books.toscrape.com/robots.txt` once — the
site returned a 404 Not Found (no robots.txt file exists). A missing file is not the
same as explicit permission, so this scraper stays limited to the sandbox's own stated
purpose and the 3-page scope above, and sends an honest identifying user-agent on
every request.

I will not reuse this code on another site without checking its rules and terms first.

## Lane and setup

**Lane:** Python 3.10+

**Dependencies:** `requests`, `beautifulsoup4`, `pydantic`

### Run it

```bash
cd scraper
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install requests beautifulsoup4 pydantic
python src/main.py
```

This produces `output/books.json`, `output/errors.json`, and `output/run-report.json`.
On a fresh run it takes roughly 30-40 seconds (63 real requests at a 0.5s delay each).
On a rerun, most pages are served from `cache/` and it finishes in a few seconds.

## Record schema

Each validated record in `output/books.json` has:

| Field                | Type          | Notes                                      |
|-----------------------|---------------|---------------------------------------------|
| `title`               | string        | Book title                                  |
| `product_url`         | URL           | Canonical identity — used to dedupe records |
| `price_text`          | string        | Raw price as shown on the page, e.g. `£51.77` |
| `price_gbp`           | number        | Parsed numeric price, e.g. `51.77`          |
| `availability_text`   | string        | Raw stock text, e.g. `In stock (22 available)` |
| `rating_text`         | string \| null | Star rating word, e.g. `Three`             |
| `description`         | string \| null | Book description; `null` if the page has none |
| `source_page`         | URL           | Which catalogue page this book was discovered on |
| `fetched_at`          | string        | UTC timestamp of when the record was fetched |

Records are validated against this schema with Pydantic before being stored. Any
record that fails validation is written to `output/errors.json` with the reason,
instead of `books.json`.

## Politeness rules

- **User-agent:** every request identifies itself as
  `FlyRankInternshipA9/1.0 (+https://github.com/Swathy-S-08/CRUD_API-)`
- **Timeout:** every request gives up after 5 seconds rather than hanging forever
- **Delay:** at least 0.5 seconds between real requests to the site; cached pages
  need no delay since they never leave the local machine
- **Caching:** every fetched page is saved to `cache/` and read from there on later
  runs, so the site is asked for each page once during development
- **Retry rule:** a timeout or server error (5xx) is retried once; a 404 (page does
  not exist) or 403 (site said no) is never retried, since asking again would not
  help

## Sample run report

```json
{
  "start_time": "2026-09-20T17:11:11.847350+00:00",
  "duration_seconds": 3.242196,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_page_details": []
}
```

## Why no browser was needed

The book data (title, price, availability, rating, description) is already present
in the raw HTML the server sends on first response — nothing is loaded afterward by
JavaScript. A headless browser like Playwright would only add startup cost and
memory overhead here with no benefit.

## Ethics note

Scrapers should prefer an official API when one exists rather than parsing HTML.
This project only touches a site explicitly built for scraping practice, at a small,
fixed scope (3 pages, 60 books) — never a real business's site, and never anything
behind a login or paywall. Requests identify themselves honestly, go slowly, and
collect only the data needed for this assignment. None of this code should be
pointed at another site without separately checking that site's own rules and terms
first.