import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, HttpUrl

HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/Swathy-S-08/CRUD_API-)"
}
TIMEOUT = 5
DELAY = 0.5

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

BASE_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"




class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: HttpUrl
    fetched_at: str


def parse_price_gbp(price_text: str) -> float:
    # "£51.77" -> 51.77 — strip everything that isn't a digit or a dot
    cleaned = "".join(ch for ch in price_text if ch.isdigit() or ch == ".")
    return float(cleaned)




def fetch_page(url: str, cache_filename: str) -> str:
    cache_path = CACHE_DIR / cache_filename

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT — {cache_filename} ({len(html)} bytes)")
        return html

    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: {url} returned status {response.status_code}")

    response.encoding = "utf-8"
    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH — {cache_filename} ({len(html)} bytes)")

    time.sleep(DELAY)
    return html


def discover_catalogue_pages_and_books(start_url: str, max_pages: int = 3) -> list[str]:
    all_book_urls = []
    current_url = start_url
    page_number = 1

    while current_url and page_number <= max_pages:
        cache_filename = f"catalogue-page-{page_number}.html"
        html = fetch_page(current_url, cache_filename)
        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod"):
            relative_href = article.select_one("h3 a")["href"]
            absolute_url = urljoin(current_url, relative_href)
            all_book_urls.append(absolute_url)

        next_link = soup.select_one("li.next a")
        if next_link and page_number < max_pages:
            current_url = urljoin(current_url, next_link["href"])
            page_number += 1
        else:
            current_url = None

    unique_urls = list(dict.fromkeys(all_book_urls))
    print(f"catalogue_pages={page_number} discovered={len(all_book_urls)} unique_urls={len(unique_urls)}")
    return unique_urls


def book_url_to_cache_filename(book_url: str) -> str:
    slug = book_url.rstrip("/").split("/")[-2]
    return f"book-{slug}.html"


def extract_book_record(book_url: str, source_page: str) -> dict:
    cache_filename = book_url_to_cache_filename(book_url)
    html = fetch_page(book_url, cache_filename)
    soup = BeautifulSoup(html, "html.parser")

    product_main = soup.select_one("div.product_main")

    title = product_main.select_one("h1").get_text(strip=True)
    price_text = product_main.select_one("p.price_color").get_text(strip=True)
    availability_text = product_main.select_one("p.instock.availability").get_text(strip=True)

    rating_tag = product_main.select_one("p.star-rating")
    rating_text = rating_tag["class"][1] if rating_tag else None

    description_tag = soup.select_one("#product_description")
    if description_tag:
        description = description_tag.find_next_sibling("p").get_text(strip=True)
    else:
        description = None

    return {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }



def normalize_and_validate(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    seen_urls = set()
    valid_records = []
    invalid_records = []

    for raw in raw_records:
        # dedupe by canonical URL — if we've already kept this one, skip
        if raw["product_url"] in seen_urls:
            continue

        try:
            raw_with_price = {**raw, "price_gbp": parse_price_gbp(raw["price_text"])}
            record = BookRecord(**raw_with_price)
            valid_records.append(record.model_dump(mode="json"))
            seen_urls.add(raw["product_url"])
        except (ValidationError, ValueError) as e:
            invalid_records.append({
                "product_url": raw.get("product_url"),
                "reason": str(e),
            })

    return valid_records, invalid_records


if __name__ == "__main__":
    book_urls = discover_catalogue_pages_and_books(BASE_CATALOGUE_URL)

    raw_records = []
    for url in book_urls:
        raw_records.append(extract_book_record(url, source_page=BASE_CATALOGUE_URL))

    print(f"detail_pages={len(raw_records)}")

    valid_records, invalid_records = normalize_and_validate(raw_records)

    books_path = OUTPUT_DIR / "books.json"
    errors_path = OUTPUT_DIR / "errors.json"

    books_path.write_text(
        __import__("json").dumps(valid_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    errors_path.write_text(
        __import__("json").dumps(invalid_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"valid_records={len(valid_records)} invalid_records={len(invalid_records)}")