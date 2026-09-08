## Target classification

**Site:** books.toscrape.com

**Why this target is appropriate:** Books to Scrape is a public sandbox site built 
specifically for people to practice web scraping on. It exists for exactly this kind 
of exercise — no real business, personal data, or paywalled content is involved.

**Scope:** This scraper only touches the first 3 catalogue pages (60 books total). 
It does not crawl the entire site.

**Data collected:** For each book — title, price, availability, star rating, 
description, and the product page URL. All fields are already present in the 
HTML the server sends; no login or hidden data is involved.

**robots.txt result:** Requested `https://books.toscrape.com/robots.txt` once — 
the site returned a 404 Not Found (no robots.txt file exists). A missing file is 
not the same as explicit permission, so this scraper stays limited to the sandbox's 
own stated purpose and the 3-page scope above, and sends an honest identifying 
user-agent on every request.

I will not reuse this code on another site without checking its rules and terms first.