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
        domain TEXT,
        tags TEXT[],
        embedding vector(384)
    );
    """)
    conn.commit()

def save_article(conn, title, url, text, domain, tags):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO articles (title, url, text, domain, tags) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING",
        (title, url, text, domain, tags)
    )
    conn.commit()

def save_embedding(conn, url, embedding):
    cur = conn.cursor()
    cur.execute(
        "UPDATE articles SET embedding = %s WHERE url = %s",
        (embedding.tolist(), url)
    )
    conn.commit()

def find_similar_article(conn, embedding, threshold=0.15):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT title, embedding <=> %s::vector AS distance
        FROM articles
        WHERE embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT 1;
        """,
        (embedding.tolist(),)
    )
    result = cur.fetchone()
    if result and result[1] < threshold:
        print(f"    [dedup] distance={result[1]:.4f} matched: {result[0]}")
        return result
    return None