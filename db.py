import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost", port=5432, dbname="postgres",
        user="postgres", password="devpassword"
    )

def setup_tables(conn):
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT UNIQUE,
        text TEXT,
        embedding vector(384)
    );
    """)
    conn.commit()

def save_article(conn, title, url, text):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (title, url, text) VALUES (%s, %s, %s) ON CONFLICT (url) DO NOTHING",
        (title, url, text)
    )
    conn.commit()

def save_embedding(conn, url, embedding):
    cur = conn.cursor()
    cur.execute(
        "UPDATE articles SET embedding = %s WHERE url = %s",
        (embedding.tolist(), url)
    )
    conn.commit()