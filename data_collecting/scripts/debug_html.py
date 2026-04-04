import cloudscraper
from bs4 import BeautifulSoup

scraper_session = cloudscraper.create_scraper()
scraper_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/"
})

url = "https://www.khmer24.com/en/c-room-for-rent?page=1"
response = scraper_session.get(url, timeout=15)
soup = BeautifulSoup(response.text, "html.parser")

# Save full HTML so you can inspect it
with open("debug_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Status:", response.status_code)
print("Page title:", soup.title.text if soup.title else "No title")
print("\n--- All <a> tags with /en/ in href (first 20) ---")
for a in soup.find_all("a", href=True)[:40]:
    href = a["href"]
    if "/en/" in href:
        print(repr(a.get("class")), "->", href)


# Add at the bottom of debug_html.py
detail_url = "https://www.khmer24.com/en/rooms-for-rent-adid-12447311"
detail_response = scraper_session.get(detail_url, timeout=15)
detail_soup = BeautifulSoup(detail_response.text, "html.parser")

with open("debug_detail.html", "w", encoding="utf-8") as f:
    f.write(detail_response.text)

print("\n--- Detail page title ---")
print(detail_soup.title.text if detail_soup.title else "No title")

print("\n--- All text-bearing tags with likely field info ---")
for tag in detail_soup.select("span, div, p, h1, h2"):
    text = tag.get_text(strip=True)
    if text and len(text) < 80:
        print(repr(tag.get("class")), "->", text)