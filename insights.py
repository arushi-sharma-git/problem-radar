"""
insights.py — Week 3: insight extraction + idea generation

Pipeline (per cluster):
    cluster articles -> insight_extraction() -> Insight (JSON, validated)
    Insight -> idea_generation() -> IdeaList (JSON, validated)

Depends on:
    - db.get_connection()  (existing db.py)
    - llm.generate(prompt, temperature=...)  (existing llm.py, with the
      temperature param added)
    - schemas.py (Insight, IdeaList) — pydantic validation
    - prompts/insight_v1.txt, prompts/idea_v1.txt — versioned prompt templates
"""

import os
import json
import re
import time
from pydantic import ValidationError

from db import get_connection, setup_insights_tables, save_insight, save_ideas
from llm import generate as call_gemini
from schemas import Insight, IdeaList

PROMPT_DIR = "prompts"
CACHE_DIR = "cache"
INSIGHT_PROMPT_VERSION = "v1"
IDEA_PROMPT_VERSION = "v1"
SECONDS_BETWEEN_LLM_CALLS = 8  # stay under the free-tier per-minute cap


# ---------- Shared helpers ----------

def load_prompt_template(name):
    path = os.path.join(PROMPT_DIR, f"{name}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def strip_json_fences(text):
    """LLMs sometimes wrap JSON in ```json ... ``` even when told not to."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def call_and_validate(prompt, schema_model, temperature, max_validation_retries=1):
    """
    Calls the LLM, parses+validates the JSON against schema_model.
    If validation fails, retries once with the error appended to the prompt
    (per the prompt-engineering guide's advice).
    """
    current_prompt = prompt
    last_error = None

    for attempt in range(max_validation_retries + 1):
        raw = call_gemini(current_prompt, temperature=temperature)
        time.sleep(SECONDS_BETWEEN_LLM_CALLS)
        cleaned = strip_json_fences(raw)
        try:
            data = json.loads(cleaned)
            return schema_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            if attempt < max_validation_retries:
                current_prompt = (
                    prompt
                    + f"\n\nYour last response failed validation because: {e}. "
                      f"Return valid JSON only, matching the schema exactly."
                )
            else:
                raise RuntimeError(f"Validation failed after retry: {last_error}\nLast raw output: {raw}")


def cache_path(kind, cluster_id, version):
    os.makedirs(os.path.join(CACHE_DIR, kind), exist_ok=True)
    return os.path.join(CACHE_DIR, kind, f"cluster_{cluster_id}_{version}.json")


def load_from_cache(kind, cluster_id, version):
    path = cache_path(kind, cluster_id, version)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_to_cache(kind, cluster_id, version, data_dict):
    path = cache_path(kind, cluster_id, version)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2)


# ---------- Hour 2-3: fetch excerpts + build insight prompt ----------

def fetch_cluster_excerpts(article_ids, snippet_words=150):
    """Pulls title, url, and a ~150-word snippet for each article id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, url, text FROM articles WHERE id = ANY(%s)",
        (article_ids,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    excerpts = []
    for article_id, title, url, text in rows:
        words = (text or "").split()
        snippet = " ".join(words[:snippet_words])
        excerpts.append({
            "id": str(article_id),
            "title": title,
            "url": url,
            "snippet": snippet,
        })
    return excerpts


def build_insight_prompt(cluster_id, excerpts):
    template = load_prompt_template(f"insight_{INSIGHT_PROMPT_VERSION}")
    excerpt_lines = "\n".join(
        f"[EXCERPT id={e['id']}] {e['title']} — {e['snippet']} — source: {e['url']}"
        for e in excerpts
    )
    return template.format(n=len(excerpts), cluster_id=cluster_id, excerpts=excerpt_lines)


def insight_extraction(cluster_id, article_ids, use_cache=True):
    if use_cache:
        cached = load_from_cache("insights", cluster_id, INSIGHT_PROMPT_VERSION)
        if cached:
            print(f"Cluster {cluster_id}: insight loaded from cache")
            return Insight.model_validate(cached)

    excerpts = fetch_cluster_excerpts(article_ids)
    prompt = build_insight_prompt(cluster_id, excerpts)
    insight = call_and_validate(prompt, Insight, temperature=0.25)

    save_to_cache("insights", cluster_id, INSIGHT_PROMPT_VERSION, insight.model_dump())
    return insight


# ---------- Hour 7-8: idea generation ----------

def build_idea_prompt(insight: Insight):
    template = load_prompt_template(f"idea_{IDEA_PROMPT_VERSION}")
    return template.format(
        domain=insight.domain,
        pain_point=insight.pain_point,
        affected_group=insight.affected_group,
        evidence_gap=insight.evidence_gap,
    )


def idea_generation(cluster_id, insight: Insight, use_cache=True):
    if use_cache:
        cached = load_from_cache("ideas", cluster_id, IDEA_PROMPT_VERSION)
        if cached:
            print(f"Cluster {cluster_id}: ideas loaded from cache")
            return IdeaList.model_validate(cached)

    prompt = build_idea_prompt(insight)
    idea_list = call_and_validate(prompt, IdeaList, temperature=0.7)

    save_to_cache("ideas", cluster_id, IDEA_PROMPT_VERSION, idea_list.model_dump())
    return idea_list


# ---------- Hour 5-6 & orchestration ----------

def process_cluster(cluster_id, article_ids, use_cache=True):
    print(f"\n=== Cluster {cluster_id} ({len(article_ids)} articles) ===")

    insight = insight_extraction(cluster_id, article_ids, use_cache=use_cache)
    print(f"Insight: {insight.pain_point} (confidence: {insight.confidence})")

    ideas = idea_generation(cluster_id, insight, use_cache=use_cache)
    for idea in ideas.ideas:
        print(f"  - [{idea.difficulty}] {idea.problem_statement}")

    # Persist to Postgres regardless of whether the above came from cache or
    # a fresh API call — the DB is the source of truth the API will read from.
    conn = get_connection()
    insight_id = save_insight(conn, cluster_id, article_ids, insight)
    save_ideas(conn, insight_id, ideas.ideas)
    conn.close()
    print(f"  [saved to Postgres: insight_id={insight_id}]")

    return insight, ideas


if __name__ == "__main__":
    from cluster import load_embeddings, reduce_dimensions, run_hdbscan, get_cluster_article_map

    setup_conn = get_connection()
    setup_insights_tables(setup_conn)
    setup_conn.close()

    article_ids, embeddings, metadata = load_embeddings()
    reduced = reduce_dimensions(embeddings)
    labels, _ = run_hdbscan(reduced)
    cluster_map = get_cluster_article_map(article_ids, labels)

    print(f"\nProcessing {len(cluster_map)} clusters for insight + idea generation...\n")
    all_results = {}
    for cluster_id, ids_in_cluster in cluster_map.items():
        insight, ideas = process_cluster(cluster_id, ids_in_cluster)
        all_results[cluster_id] = {"insight": insight.model_dump(), "ideas": ideas.model_dump()}

    print(f"\nDone. {len(all_results)} clusters processed. Cached under cache/insights/ and cache/ideas/.")