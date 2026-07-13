
import feedparser
import requests

candidates = [
    ("EurekAlert!", "https://www.eurekalert.org/rss.xml"),
    ("NASA Climate", "https://climate.nasa.gov/news/rss.xml"),
    ("Yale Environment 360", "https://e360.yale.edu/feed"),
    ("UN Environment", "https://www.unep.org/feed/news.xml"),
    ("NIH Research", "https://www.nih.gov/news-events/news-releases/feed"),
    ("MedPage Today", "https://www.medpagetoday.com/feed"),
    ("Brookings", "https://www.brookings.edu/feed/"),
    ("Code for America", "https://codeforamerica.org/feed/"),
    ("Stanford SSIR", "https://ssir.org/feed"),
    ("CFR", "https://www.cfr.org/rss"),
    ("Pew Research", "https://www.pewresearch.org/feed/"),
    ("IMF Blog", "https://www.imf.org/en/Blogs/Blogfeed"),
    ("World Bank", "https://www.worldbank.org/en/news/feed"),
    ("The Economist Finance", "https://www.economist.com/finance-and-economics/rss.xml"),
    ("Edutopia", "https://www.edutopia.org/feed"),
    ("Inside Higher Ed", "https://www.insidehighered.com/feed"),
    ("Chronicle of Higher Ed", "https://www.chronicle.com/feed"),
    ("Berkman Klein", "https://cyber.harvard.edu/rss.xml"),
    ("FlowingData", "https://flowingdata.com/feed"),
    ("Wired", "https://www.wired.com/feed/rss")
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

fixed = []
still_broken = []

for name, url in candidates:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
        if feed.entries:
            fixed.append((name, url, len(feed.entries), response.status_code))
        else:
            still_broken.append((name, url, response.status_code))
    except Exception as e:
        still_broken.append((name, url, f"error: {e}"))

print(f"\n✅ FIXED BY USER-AGENT ({len(fixed)}):")
for name, url, count, status in fixed:
    print(f"  {name}: {count} entries (status {status})")

print(f"\n❌ STILL BROKEN ({len(still_broken)}):")
for name, url, status in still_broken:
    print(f"  {name}: status/error = {status}")