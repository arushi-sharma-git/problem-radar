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

def setup_insights_tables(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS insights (
        id SERIAL PRIMARY KEY,
        cluster_id INTEGER UNIQUE NOT NULL,
        domain TEXT,
        pain_point TEXT,
        affected_group TEXT,
        evidence_gap TEXT,
        confidence TEXT,
        article_ids INTEGER[],
        created_at TIMESTAMP DEFAULT now()
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ideas (
        id SERIAL PRIMARY KEY,
        insight_id INTEGER REFERENCES insights(id) ON DELETE CASCADE,
        problem_statement TEXT,
        target_user TEXT,
        suggested_approach TEXT,
        tech_angle TEXT,
        difficulty TEXT,
        feasibility_score INTEGER,
        impact_score INTEGER
    );
    """)
    conn.commit()


def save_insight(conn, cluster_id, article_ids, insight):
    """insight: an Insight pydantic model (or anything with the same attributes).
    Upserts by cluster_id so reruns update rather than duplicate.
    Returns the insight's DB id."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO insights (cluster_id, domain, pain_point, affected_group, evidence_gap, confidence, article_ids)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (cluster_id) DO UPDATE SET
            domain = EXCLUDED.domain,
            pain_point = EXCLUDED.pain_point,
            affected_group = EXCLUDED.affected_group,
            evidence_gap = EXCLUDED.evidence_gap,
            confidence = EXCLUDED.confidence,
            article_ids = EXCLUDED.article_ids
        RETURNING id;
        """,
        (cluster_id, insight.domain, insight.pain_point, insight.affected_group,
         insight.evidence_gap, insight.confidence, article_ids)
    )
    insight_id = cur.fetchone()[0]
    conn.commit()
    return insight_id


def save_ideas(conn, insight_id, ideas):
    """ideas: a list of Idea pydantic models (or anything with the same attributes).
    Clears any previously stored ideas for this insight_id first, so reruns
    don't accumulate duplicates."""
    cur = conn.cursor()
    cur.execute("DELETE FROM ideas WHERE insight_id = %s", (insight_id,))
    for idea in ideas:
        cur.execute(
            """
            INSERT INTO ideas (insight_id, problem_statement, target_user, suggested_approach,
                                tech_angle, difficulty, feasibility_score, impact_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (insight_id, idea.problem_statement, idea.target_user, idea.suggested_approach,
             idea.tech_angle, idea.difficulty, idea.feasibility_score, idea.impact_score)
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