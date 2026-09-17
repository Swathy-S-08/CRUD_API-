import requests
from pathlib import Path

# Polite identification — replace with your actual repo URL
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/Swathy-S-08/CRUD_API-)"
}
TIMEOUT = 5  # seconds

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def fetch_page(url: str, cache_filename: str) -> str:
    cache_path = CACHE_DIR / cache_filename

    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8")
        print(f"CACHE HIT — {cache_filename} ({len(html)} bytes)")
        return html

    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: {url} returned status {response.status_code}")

    html = response.text
    cache_path.write_text(html, encoding="utf-8")
    print(f"FETCH — {cache_filename} ({len(html)} bytes)")
    return html


if __name__ == "__main__":
    fetch_page(
        "https://books.toscrape.com/catalogue/page-1.html",
        "catalogue-page-1.html"
    )