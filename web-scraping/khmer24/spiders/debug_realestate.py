# khmer24/spiders/debug_realestate.py
import scrapy
from scrapy_playwright.page import PageMethod
from bs4 import BeautifulSoup


class DebugRealestateSpider(scrapy.Spider):
    name = "debug_realestate"

    START_URL = "https://www.realestate.com.kh/rent/phnom-penh/house/?active_tab=popularLocations&categories=House&order_by=relevance&property_type=residential&q=location%3A%20Phnom%20Penh&search_type=rent"

    def start_requests(self):
        yield scrapy.Request(
            url=self.START_URL,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_context": "default",
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 5000),
                ],
            },
            errback=self.errback,
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]

        # Save screenshot to see what page looks like
        await page.screenshot(path="debug_realestate.png", full_page=True)
        self.logger.info("Saved debug_realestate.png")

        # Scroll once to trigger lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)

        content = await page.content()
        await page.close()

        soup = BeautifulSoup(content, "html.parser")

        # Save full HTML
        with open("debug_realestate.html", "w", encoding="utf-8") as f:
            f.write(content)
        self.logger.info("Saved debug_realestate.html")

        # Print page title
        self.logger.info(f"Page title: {soup.title.text if soup.title else 'No title'}")

        # Find all anchor tags that look like listing cards
        self.logger.info("\n--- All <a> tags with likely listing hrefs ---")
        for a in soup.find_all("a", href=True)[:50]:
            href = a.get("href", "")
            classes = a.get("class", [])
            if any(k in href for k in ["/rent/", "/buy/", "/property/", "listing", "adid"]):
                self.logger.info(f"classes={classes} -> {href}")

        # Find likely listing card containers
        self.logger.info("\n--- Likely listing card elements ---")
        for tag in soup.select("article, .card, .listing, .property, [class*='card'], [class*='listing'], [class*='property']"):
            self.logger.info(f"tag={tag.name} classes={tag.get('class')} text_preview={tag.get_text(strip=True)[:80]}")

        # Print first listing detail if found
        self.logger.info("\n--- Sample text content (short tags) ---")
        for tag in soup.select("h1, h2, h3, span, p"):
            text = tag.get_text(strip=True)
            if text and len(text) < 100:
                self.logger.info(f"{tag.name} classes={tag.get('class')} -> {text}")

    async def errback(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()
        self.logger.error(f"Failed: {failure.request.url} — {failure.value}")