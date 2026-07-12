import feedparser
import trafilatura

from db import get_connection, setup_tables, save_article, save_embedding
from embed import get_embedding
from llm import summarize

feed = feedparser.parse("http://feeds.bbci.co.uk/news/world/rss.xml")

conn = get_connection()
setup_tables(conn)

for entry in feed.entries[:5]:
    downloaded = trafilatura.fetch_url(entry.link)
    text = trafilatura.extract(downloaded)
    if not text:
        continue

    save_article(conn, entry.title, entry.link, text)
    embedding = get_embedding(text)
    save_embedding(conn, entry.link, embedding)

    print(entry.title)

print("\nSample summary:")
print(summarize(feed.entries[0].title + ". " + trafilatura.extract(trafilatura.fetch_url(feed.entries[0].link))))