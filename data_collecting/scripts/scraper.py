# scripts/scraper.py
import cloudscraper
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from scripts.config import COLUMNS

scraper_session = cloudscraper.create_scraper()
# HEADERS = {
# 	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
# 	"AppleWebKit/537.36 (KHTML, like Gecko) "
# 	"Chrome/120.0.0.0 Safari/537.36"
# }
BASE_URL = "https://www.khmer24.com"


def get_soup(url):
    """Fetch a page and return a BeautifulSoup object."""
    try:
        response = scraper_session.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
def scrape_listing_urls(page_url):
	"""Extract individual listing URLs from a search results page."""
	soup = get_soup(page_url)
	if not soup:
		return []
	links = []
	# Accurate selector for Khmer24 room-for-rent cards
	for a in soup.select("a.post"):
		href = a.get("href", "")
		if href and href.startswith("/"):
			links.append(BASE_URL + href)
		elif href.startswith("http"):
			links.append(href)
	return list(set(links))  # Remove duplicates


def scrape_listing_detail(url):
    """Scrape one listing page and return a dict of fields."""
    soup = get_soup(url)
    if not soup:
        return None
    try:
        # Title
        title_tag = soup.select_one(".font-semibold.text-3xl")

        # Price
        price_tag = soup.select_one(".text-error-500.text-2xl")

        # Location — second "flex gap-x-1 items-center" span (first is the ID)
        location_tags = soup.select(".flex.gap-x-1.items-center")
        loc_tag = location_tags[1] if len(location_tags) > 1 else None

        # Detail grid: "Main Category | Category | Size"
        grid = soup.select_one(".grid.gap-x-6.gap-y-4.grid-cols-4")
        grid_items = grid.select(".flex.gap-x-3") if grid else []

        size_text = None
        type_text = None
        category_text = None
        if grid:
            for item in grid.select("div"):
                text = item.get_text(strip=True)
                if "m²" in text:
                    size_text = text
                elif text.startswith("Room For Rent") or text.startswith("House") or text.startswith("Condo"):
                    type_text = text

        # Full address line below the map section
        address_tag = soup.select_one(".text-sm")

        return {
            COLUMNS["price"]: price_tag.get_text(strip=True) if price_tag else None,
            COLUMNS["city"]: loc_tag.get_text(strip=True).split(",")[-1].strip() if loc_tag else None,
            COLUMNS["location"]: loc_tag.get_text(strip=True) if loc_tag else None,
            COLUMNS["type"]: type_text,
            COLUMNS["size"]: size_text,
            COLUMNS["bedrooms"]: None,   # Not visible in detail page HTML
            COLUMNS["bathrooms"]: None,  # Not visible in detail page HTML
            COLUMNS["furnished"]: None,  # Not visible in detail page HTML
            "source_url": url,
            "title": title_tag.get_text(strip=True) if title_tag else None,
            "address": address_tag.get_text(strip=True) if address_tag else None,
        }
    except Exception as e:
        print(f"Parse error on {url}: {e}")
        return None
    

# --- MAIN SCRAPER ROUTINE ---
def main():
    """Scrape Khmer24 room-for-rent listings and save to raw CSV."""
    from scripts.config import DATA_PATH
    START_URL = "https://www.khmer24.com/en/c-room-for-rent"
    seen_urls = set()
    all_rows = []
    page = 1
    max_empty_pages = 3
    empty_count = 0

    while True:
        # --- TEMPORARY: stop after page 1 for testing ---
        if page > 1:
            print("Test mode: stopping after page 1.")
            break
        # -------------------------------------------------

        page_url = f"{START_URL}?page={page}"
        print(f"Scraping page {page}: {page_url}")
        listing_urls = scrape_listing_urls(page_url)
        if not listing_urls:
            empty_count += 1
            if empty_count >= max_empty_pages:
                print("No more listings found. Stopping.")
                break
            page += 1
            continue
        empty_count = 0
        for url in listing_urls:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            row = scrape_listing_detail(url)
            if row:
                all_rows.append(row)
                print(f"  Scraped: {url}")
            time.sleep(random.uniform(1.5, 2.5))
        page += 1

    if all_rows:
        df = pd.DataFrame(all_rows)
        raw_dir = os.path.join(os.path.dirname(DATA_PATH), "raw")
        os.makedirs(raw_dir, exist_ok=True)
        raw_csv = os.path.join(raw_dir, "raw_listings.csv")
        df.to_csv(raw_csv, index=False)
        print(f"\nSaved {len(df)} listings to {raw_csv}")
        print(df.head())
    else:
        print("No listings scraped.")


if __name__ == "__main__":
	main()