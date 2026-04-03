# khmer24/spiders/realestate_kh.py
import scrapy
from scrapy_playwright.page import PageMethod
from bs4 import BeautifulSoup


class RealestateKhSpider(scrapy.Spider):
    name = "realestate_kh"

    BASE_URL = "https://www.realestate.com.kh"
    START_URL = "https://www.realestate.com.kh/rent/chroy-changvar/house/"
    QUERY_PARAMS = "?active_tab=popularLocations&categories=House&order_by=relevance&property_type=residential&q=location%3A%20Phnom%20Penh%20%3E%20Chroy%20Changvar&search_type=rent"

    def start_requests(self):
        yield scrapy.Request(
            url=self.START_URL + self.QUERY_PARAMS,
            callback=self.parse_listings,
            meta={
                "playwright": True,
                "playwright_context": "default",
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", ".item", timeout=30000),
                ],
                "page_num": 1,
            },
            errback=self.errback,
        )

    async def parse_listings(self, response):
        page = response.meta["playwright_page"]
        page_num = response.meta["page_num"]
        content = await page.content()
        await page.close()

        soup = BeautifulSoup(content, "html.parser")

        listing_urls = []
        for item in soup.select(".item"):
            header_link = item.select_one("header a[href]")
            if header_link:
                href = header_link.get("href", "")
                if href.startswith("/"):
                    listing_urls.append(self.BASE_URL + href)
                elif href.startswith("http"):
                    listing_urls.append(href)

        self.logger.info(f"Page {page_num}: found {len(listing_urls)} listings")

        for url in listing_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={
                    "playwright": True,
                    "playwright_context": "default",
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".info", timeout=15000),
                    ],
                },
                errback=self.errback,
            )

        next_page_num = page_num + 1
        if next_page_num <= 50:
            next_url = f"{self.START_URL}{self.QUERY_PARAMS}&page={next_page_num}"
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_listings,
                meta={
                    "playwright": True,
                    "playwright_context": "default",
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".item", timeout=30000),
                    ],
                    "page_num": next_page_num,
                },
                errback=self.errback,
            )

    async def parse_detail(self, response):
        page = response.meta["playwright_page"]
        content = await page.content()
        await page.close()

        soup = BeautifulSoup(content, "html.parser")

        title_tag = soup.select_one(".heading")
        title = title_tag.get_text(strip=True) if title_tag else None

        price_tag = soup.select_one(".value")
        price = price_tag.get_text(strip=True) if price_tag else None

        property_type = None
        if title_tag:
            property_type = title_tag.get_text(strip=True).split("\n")[0].strip()

        bedrooms   = None
        bathrooms  = None
        floor_area = None
        land_area  = None

        detail_block = soup.select_one(".css-r7o7s2")
        if detail_block:
            for item in detail_block.select("div"):
                value_tag = item.select_one("span.value")
                label_tag = item.select_one("span.text")
                if not value_tag or not label_tag:
                    continue
                value = value_tag.get_text(strip=True)
                label = label_tag.get_text(strip=True)
                if "Bedroom" in label:
                    bedrooms = value
                elif "Bathroom" in label:
                    bathrooms = value
                elif "Floor Area" in label or "floor area" in label.lower():
                    floor_area = value
                elif "Land Area" in label or "land area" in label.lower():
                    land_area = value

        desc_tag = soup.select_one(".css-zrj3zm")
        furnished = None
        if desc_tag:
            desc_text = desc_tag.get_text(" ", strip=True)
            if any(k in desc_text for k in ["Fully Furnished", "fully furnished", "Fully furnished"]):
                furnished = "Fully Furnished"
            elif any(k in desc_text for k in ["Partly Furnished", "Semi Furnished", "partly furnished"]):
                furnished = "Partly Furnished"
            elif any(k in desc_text for k in ["Unfurnished", "unfurnished"]):
                furnished = "Unfurnished"
            else:
                furnished = "Unknown"

        yield {
            "rent_price_usd": price,
            "city":           "Phnom Penh",
            "district":       "Chroy Changvar",
            "property_type":  property_type,
            "size_sqm":       floor_area,
            "land_area":      land_area,
            "bedrooms":       bedrooms,
            "bathrooms":      bathrooms,
            "furnished":      furnished,
            "title":          title,
            "source_url":     response.url,
        }

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Request failed: {failure.request.url} — {failure.value}")