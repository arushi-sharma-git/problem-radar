"""
cluster.py — Week 2 of problem-radar

Pipeline:
  1. Load all article embeddings from Postgres/pgvector into a NumPy matrix
  2. Reduce dimensionality with UMAP
  3. Cluster with HDBSCAN
  4. Ask Gemini to name/tag each cluster based on representative articles
  5. Print (or persist) cluster -> theme -> article mapping

Matches your actual db.py / llm.py:
  - db.get_connection() -> psycopg2 connection
  - articles table: id, title, url, text, domain, tags, embedding (vector(384))
  - llm.generate(prompt) -> str  (added alongside summarize(), same retry logic)
"""

import numpy as np
from pgvector.psycopg2 import register_vector  # pip install pgvector
import umap
import hdbscan
import time
import argparse

from db import get_connection
from llm import generate as call_gemini

SECONDS_BETWEEN_LLM_CALLS = 15  # keeps us under the 5-requests/minute free-tier cap


# ---------- Step 1: Load embeddings ----------

def load_embeddings():
    """
    Returns:
        article_ids: list[int], length n
        embeddings:  np.ndarray, shape (n, 384)
        metadata:    list[dict] with keys id, title, domain, tags
                     (same order as article_ids/embeddings)
    """
    conn = get_connection()
    register_vector(conn)  # tells psycopg2 how to turn the pgvector column
                            # into a numpy array automatically, instead of
                            # a raw "[0.1, -0.2, ...]" string

    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, domain, tags, embedding
        FROM articles
        WHERE embedding IS NOT NULL
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        raise RuntimeError("No articles with embeddings found — check your DB.")

    article_ids = []
    metadata = []
    vectors = []

    for row in rows:
        article_id, title, domain, tags, embedding = row
        article_ids.append(article_id)
        metadata.append({
            "id": article_id,
            "title": title,
            "domain": domain,
            "tags": tags,
        })
        # With register_vector, `embedding` already comes back as a numpy
        # array. If you're NOT using the pgvector adapter for some reason,
        # fall back to parsing the string form:
        # register_vector can return a few different shapes depending on
        # your pgvector-python version:
        #   - a numpy array directly (newer versions)
        #   - a pgvector.Vector object with a .to_numpy() method (common case —
        #     this is what caused the "dim 1" / "float() ... not Vector" error)
        #   - a raw string like "[0.1, -0.2, ...]" (no adapter registered)
        if hasattr(embedding, "to_numpy"):
            vec = embedding.to_numpy()
        elif isinstance(embedding, str):
            vec = np.fromstring(embedding.strip("[]"), sep=",")
        else:
            vec = np.asarray(embedding, dtype=np.float64)
        vectors.append(vec)

    embeddings = np.vstack(vectors)
    if embeddings.shape[1] != 384:
        raise RuntimeError(
            f"Expected 384-dim embeddings (MiniLM-L6-v2), got shape {embeddings.shape}. "
            "This usually means the pgvector value wasn't unpacked correctly — "
            "check what type(embedding) is for a single row."
        )
    print(f"Loaded {embeddings.shape[0]} embeddings of dim {embeddings.shape[1]}")
    return article_ids, embeddings, metadata


# ---------- Step 2: UMAP dimensionality reduction ----------

def reduce_dimensions(embeddings, n_components=10, n_neighbors=5, min_dist=0.0):
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="cosine",
        random_state=42,
    )
    reduced = reducer.fit_transform(embeddings)
    print(f"UMAP reduced to shape {reduced.shape}")
    return reduced


# ---------- Step 3: HDBSCAN clustering ----------

def run_hdbscan(reduced_embeddings, min_cluster_size=3, min_samples=None):
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",  # euclidean on UMAP output, not cosine on raw
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(reduced_embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))
    print(f"HDBSCAN found {n_clusters} clusters, {n_noise} noise points "
          f"out of {len(labels)} articles")
    return labels, clusterer


# ---------- Step 4: LLM-based cluster tagging ----------

def get_representative_articles(cluster_indices, embeddings, metadata, k=6):
    """
    Picks up to k articles closest to the cluster centroid, so the LLM
    prompt sees the most 'typical' articles rather than a random sample.
    """
    cluster_embeddings = embeddings[cluster_indices]
    centroid = cluster_embeddings.mean(axis=0)
    dists = np.linalg.norm(cluster_embeddings - centroid, axis=1)
    order = np.argsort(dists)[:k]
    chosen = [cluster_indices[i] for i in order]
    return [metadata[i] for i in chosen]


def tag_cluster_with_llm(representative_articles):
    titles = "\n".join(f"- {a['title']} (domain: {a['domain']})"
                        for a in representative_articles)

    prompt = f"""You are analyzing a cluster of news/blog articles that were
grouped together by embedding similarity. Here are representative titles
from this cluster:

{titles}

Based on these, respond in this exact format:
THEME: <a short, specific theme name, 3-8 words>
DOMAIN: <one of: science, climate, technology, health, urban-planning, design, finance, society, or 'cross-domain' if it spans several>
SUMMARY: <1-2 sentence description of what unifies this cluster>
"""
    response_text = call_gemini(prompt)  # <-- adjust to match your llm.py signature
    return response_text


# ---------- Step 5: Orchestration ----------

def main(n_neighbors=5, min_cluster_size=3, skip_llm=False, print_cluster=None):
    article_ids, embeddings, metadata = load_embeddings()
    reduced = reduce_dimensions(embeddings, n_neighbors=n_neighbors)
    labels, _ = run_hdbscan(reduced, min_cluster_size=min_cluster_size)

    if skip_llm:
        print("\n--skip-llm set: not calling Gemini. Cluster sizes + sample titles:")
        unique_labels = sorted(set(labels))
        for label in unique_labels:
            indices = [i for i, l in enumerate(labels) if l == label]
            count = len(indices)
            tag = "(noise)" if label == -1 else ""

            if label == -1:
                samples = [metadata[i]["title"] for i in indices[:2]]
            else:
                samples = [a["title"] for a in get_representative_articles(indices, embeddings, metadata, k=2)]

            print(f"\n  Cluster {label} {tag}: {count} articles")
            for title in samples:
                print(f"      e.g. {title}")

        if print_cluster is not None:
            indices = [i for i, l in enumerate(labels) if l == print_cluster]
            print(f"\nTitles in cluster {print_cluster} ({len(indices)} articles):")
            for i in indices:
                print(f"  - {metadata[i]['title']}  [{metadata[i]['domain']}]")

        return labels

    unique_labels = sorted(set(labels))
    results = {}
    quota_exhausted = False

    for label in unique_labels:
        if label == -1:
            continue  # skip noise points for tagging

        cluster_indices = [i for i, l in enumerate(labels) if l == label]
        reps = get_representative_articles(cluster_indices, embeddings, metadata)

        try:
            tag_response = tag_cluster_with_llm(reps)
        except Exception as e:
            print(f"\n=== Cluster {label} ({len(cluster_indices)} articles) ===")
            print(f"LLM tagging failed, skipping for now: {e}")
            tag_response = None
            if "RESOURCE_EXHAUSTED" in str(e):
                quota_exhausted = True
                print("\nQuota exhausted — no point trying the remaining clusters "
                      "right now, they'll fail the same way. Stopping here.")
                results[label] = {
                    "size": len(cluster_indices),
                    "llm_tag": None,
                    "sample_titles": [metadata[i]["title"] for i in cluster_indices][:10],
                }
                break

        time.sleep(SECONDS_BETWEEN_LLM_CALLS)

        cluster_article_titles = [metadata[i]["title"] for i in cluster_indices]
        results[label] = {
            "size": len(cluster_indices),
            "llm_tag": tag_response,
            "sample_titles": cluster_article_titles[:10],
        }

        if tag_response is not None:
            print(f"\n=== Cluster {label} ({len(cluster_indices)} articles) ===")
            print(tag_response)

    failed_labels = [label for label, r in results.items() if r["llm_tag"] is None]
    if failed_labels and quota_exhausted:
        print(f"\n{len(failed_labels)} cluster(s) still need tagging: {failed_labels}")
        print("Quota was exhausted this run, so skipping the retry pass — "
              "rerun main() (or just the tagging step) once quota resets.")
    elif failed_labels:
        print(f"\n{len(failed_labels)} cluster(s) failed tagging: {failed_labels}")
        print("Retrying failed clusters once more...")
        for label in failed_labels:
            cluster_indices = [i for i, l in enumerate(labels) if l == label]
            reps = get_representative_articles(cluster_indices, embeddings, metadata)
            try:
                tag_response = tag_cluster_with_llm(reps)
                results[label]["llm_tag"] = tag_response
                print(f"\n=== Cluster {label} (retry succeeded) ===")
                print(tag_response)
            except Exception as e:
                print(f"Cluster {label} failed again: {e}")
                print(f"You can rerun just this cluster later — its article titles are saved in results[{label}]['sample_titles'].")
            time.sleep(SECONDS_BETWEEN_LLM_CALLS)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cluster article embeddings and tag with Gemini.")
    parser.add_argument("--n-neighbors", type=int, default=5,
                        help="UMAP n_neighbors (lower = more local/fine-grained structure)")
    parser.add_argument("--min-cluster-size", type=int, default=3,
                        help="HDBSCAN min_cluster_size (lower = more, smaller clusters)")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Only run UMAP+HDBSCAN and print cluster sizes, no Gemini calls")
    parser.add_argument("--print-cluster", type=int, default=None,
                        help="Print all article titles in this cluster label (use with --skip-llm)")
    args = parser.parse_args()

    main(n_neighbors=args.n_neighbors, min_cluster_size=args.min_cluster_size,
         skip_llm=args.skip_llm, print_cluster=args.print_cluster)