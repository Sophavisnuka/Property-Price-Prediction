# khmer24/spiders/house_rent.py
import re
import scrapy
from scrapy_playwright.page import PageMethod
from bs4 import BeautifulSoup


class HouseRentSpider(scrapy.Spider):
    name = "house_rent"

    URLS = [
        "https://www.khmer24.com/en/c-house-for-rent?province=phnom-penh&district=chrouy-changva&commune=preaek-ta-sek",
        # add more URLs here if needed
    ]

    def start_requests(self):
        for url in self.URLS:
            yield scrapy.Request(
                url=url,
                callback=self.parse_listings,
                meta={
                    "playwright": True,
                    "playwright_context": "default",
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "a.post", timeout=30000),
                    ],
                },
                errback=self.errback,
            )

    async def parse_listings(self, response):
        page = response.meta["playwright_page"]

        # Scroll to load all listings
        previous_count = 0
        no_new_count = 0

        while True:
            listings = await page.query_selector_all("a.post")
            current_count = len(listings)
            self.logger.info(f"  Listings loaded: {current_count}")

            if current_count == previous_count:
                no_new_count += 1
                if no_new_count >= 3:
                    self.logger.info("No new listings after 3 scrolls. Done scrolling.")
                    break
            else:
                no_new_count = 0

            previous_count = current_count
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)

        content = await page.content()
        await page.close()

        soup = BeautifulSoup(content, "html.parser")
        for a in soup.select("a.post"):
            href = a.get("href", "")
            if href.startswith("/"):
                url = "https://www.khmer24.com" + href
            elif href.startswith("http"):
                url = href
            else:
                continue
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={
                    "playwright": True,
                    "playwright_context": "default",
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".font-semibold.text-3xl", timeout=15000),
                    ],
                },
                errback=self.errback,
            )

    async def parse_detail(self, response):
        page = response.meta["playwright_page"]
        content = await page.content()
        await page.close()

        soup = BeautifulSoup(content, "html.parser")

        title_tag     = soup.select_one(".font-semibold.text-3xl")
        price_tag     = soup.select_one(".text-error-500.text-2xl")
        location_tags = soup.select(".flex.gap-x-1.items-center")
        loc_tag       = location_tags[1] if len(location_tags) > 1 else None
        address_tag   = soup.select_one(".text-sm")
        desc_tag      = soup.select_one("p.text-base\\/8")

        size_text = None
        type_text = None
        bedrooms  = None
        bathrooms = None
        furnished = None

        # Method 1: extract from grid dl > dt/dd tags (most reliable)
        grid = soup.select_one(".grid.gap-x-6.gap-y-4.grid-cols-4")
        if grid:
            for dl in grid.select("dl"):
                for dt in dl.select("dt"):
                    label = dt.get_text(strip=True)
                    dd = dt.find_next_sibling("dd")
                    if not dd:
                        continue
                    value = dd.get_text(strip=True)
                    if "បន្ទប់គេង" in label:
                        bedrooms = value
                    elif "បន្ទប់ទឹក" in label:
                        bathrooms = value
                    elif "ទំហំ" in label or "size" in label.lower():
                        size_text = value
                    elif any(k in label for k in ["ប្រភេទ", "type", "Type"]):
                        type_text = value

        # Method 2: fallback from description paragraph
        if desc_tag:
            desc_text = desc_tag.get_text(" ", strip=True)

            if bedrooms is None:
                match = re.search(r"បន្ទប់គេង\s*:?\s*(\d+)", desc_text)
                if not match:
                    match = re.search(r"(\d+)\s*បន្ទប់គេង", desc_text)
                if not match:
                    match = re.search(r"(\d+)\s*bed(?:room)?s?", desc_text, re.IGNORECASE)
                if not match:
                    match = re.search(r"bed(?:room)?s?\s*:?\s*(\d+)", desc_text, re.IGNORECASE)
                if match:
                    bedrooms = match.group(1)

            if bathrooms is None:
                match = re.search(r"បន្ទប់ទឹក\s*:?\s*(\d+)", desc_text)
                if not match:
                    match = re.search(r"(\d+)\s*បន្ទប់ទឹក", desc_text)
                if not match:
                    match = re.search(r"(\d+)\s*bath(?:room)?s?", desc_text, re.IGNORECASE)
                if not match:
                    match = re.search(r"bath(?:room)?s?\s*:?\s*(\d+)", desc_text, re.IGNORECASE)
                if match:
                    bathrooms = match.group(1)

            if size_text is None:
                match = re.search(r"(\d+\.?\d*\s*m\s*x\s*\d+\.?\d*\s*m)", desc_text, re.IGNORECASE)
                if not match:
                    match = re.search(r"(\d+\.?\d*\s*x\s*\d+\.?\d*\s*m)", desc_text, re.IGNORECASE)
                if not match:
                    match = re.search(r"(\d+\.?\d*\s*m²)", desc_text)
                if match:
                    size_text = match.group(1)

            # Furnished from description keywords
            if any(k in desc_text for k in [
                "មានសម្ភារៈស្រាប់", "មានគ្រឿងសង្ហារឹម",
                "fully furnished", "Fully Furnished"
            ]):
                furnished = "Fully Furnished"
            elif any(k in desc_text for k in [
                "មានសម្ភារៈខ្លះ", "partly furnished", "Partly Furnished",
                "semi furnished", "Semi Furnished"
            ]):
                furnished = "Partly Furnished"
            elif any(k in desc_text for k in [
                "គ្មានសម្ភារៈ", "unfurnished", "Unfurnished", "un-furnished"
            ]):
                furnished = "Unfurnished"
            else:
                furnished = "Unknown"

        yield {
            "rent_price_usd": price_tag.get_text(strip=True) if price_tag else None,
            "city":           loc_tag.get_text(strip=True).split(",")[-1].strip() if loc_tag else None,
            "district":       loc_tag.get_text(strip=True) if loc_tag else None,
            "property_type":  type_text,
            "size_sqm":       size_text,
            "bedrooms":       bedrooms,
            "bathrooms":      bathrooms,
            "furnished":      furnished,
            "title":          title_tag.get_text(strip=True) if title_tag else None,
            "address":        address_tag.get_text(strip=True) if address_tag else None,
            "source_url":     response.url,
        }

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Request failed: {failure.request.url} — {failure.value}")