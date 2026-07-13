import feedparser
import trafilatura
import requests

from db import get_connection, setup_tables, save_article, save_embedding, find_similar_article
from embed import get_embedding
from sources import SOURCES

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

conn = get_connection()
setup_tables(conn)

for source in SOURCES:
    print(f"\n--- Fetching: {source['name']} ({source['domain']}) ---")
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=10)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"Failed to fetch {source['name']}: {e}")
        continue

    for entry in feed.entries[:5]:
        downloaded = trafilatura.fetch_url(entry.link)
        text = trafilatura.extract(downloaded)
        if not text:
            continue

        embedding = get_embedding(text)
        duplicate = find_similar_article(conn, embedding)
        if duplicate:
            print(f"Skipping '{entry.title}' — near-duplicate of: {duplicate[0]}")
            continue

        save_article(conn, entry.title, entry.link, text, source["domain"], source["tags"])
        save_embedding(conn, entry.link, embedding)
        print(f"Saved: {entry.title}")