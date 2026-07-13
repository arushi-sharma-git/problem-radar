from celery_app import app
import feedparser
import trafilatura

from db import get_connection, setup_tables, save_article, save_embedding, find_similar_article
from embed import get_embedding
from sources import SOURCES

@app.task
def run_ingestion():
    conn = get_connection()
    setup_tables(conn)

    total_saved = 0
    for source in SOURCES:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:5]:
            downloaded = trafilatura.fetch_url(entry.link)
            text = trafilatura.extract(downloaded)
            if not text:
                continue

            embedding = get_embedding(text)
            duplicate = find_similar_article(conn, embedding)
            if duplicate:
                continue

            save_article(conn, entry.title, entry.link, text, source["domain"], source["tags"])
            save_embedding(conn, entry.link, embedding)
            total_saved += 1

    return f"Ingestion complete. Saved {total_saved} new articles."