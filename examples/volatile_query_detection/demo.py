#!/usr/bin/env python3
"""
pg_semantic_cache — Volatile Query Detection Demo
==================================================
Demonstrates how to handle time-sensitive queries correctly when using
pg_semantic_cache. Queries like "what is the current time?" produce
nearly identical embeddings every time they are asked, so the cache
would return a stale answer as a hit without application-layer detection.

Decision flow:
  query → is_volatile? ──yes──▶ call LLM directly (never cache)
                │
               no
                ▼
          embed query
                ▼
    semantic_cache.get_cached_result()
          HIT ──────────────────────▶ return cached result  (LLM call saved)
          │
        MISS
          ▼
      call LLM
          ▼
    semantic_cache.cache_query()   ← store for future similar queries

Uses:
  - sentence-transformers (all-MiniLM-L6-v2, 384 dims) for embeddings
  - Ollama (llama3.2:1b) for answer generation

Run with Docker:
  docker compose up --build
"""

import json
import os
import re
import time
from datetime import datetime

import psycopg2
import requests
from psycopg2.extras import RealDictCursor, Json
from sentence_transformers import SentenceTransformer

# ── Configuration ──────────────────────────────────────────────────────────────

DB_HOST     = os.environ.get("DB_HOST", "localhost")
DB_PORT     = int(os.environ.get("DB_PORT", 5435))
DB_NAME     = os.environ.get("DB_NAME", "postgres")
DB_USER     = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

OLLAMA_HOST          = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL            = os.environ.get("LLM_MODEL", "llama3.2:1b")
EMBEDDING_MODEL      = "all-MiniLM-L6-v2"   # 384 dimensions
SIMILARITY_THRESHOLD = 0.80
DEFAULT_TTL          = 3600                  # seconds

# ── Volatile patterns ──────────────────────────────────────────────────────────
# Queries whose correct answer changes with time or live state should never
# be cached. Detection happens before any embedding is computed or any DB
# round-trip is made.

VOLATILE_PATTERNS = [
    r"\bwhat.{0,10}time\b",
    r"\bcurrent\s+time\b",
    r"\bright\s+now\b",
    r"\btoday.{0,10}date\b",
    r"\bcurrent\s+date\b",
    r"\blatest\s+news\b",
    r"\bbreaking\s+news\b",
    r"\bcurrent\s+(weather|temperature|price|stock|rate|score)\b",
    r"\bweather\b.{0,15}\b(today|now|currently|right now)\b",
    r"\bstock\s+price\b",
    r"\blive\s+(score|update|feed|result)\b",
    r"\bmy\s+(location|ip\s+address|position)\b",
]

_volatile_re = re.compile("|".join(VOLATILE_PATTERNS), re.IGNORECASE)


def is_volatile(query: str) -> bool:
    """Return True when the query result changes with time and must not be cached."""
    return bool(_volatile_re.search(query))


# ── LLM (Ollama) ───────────────────────────────────────────────────────────────

def pull_model():
    """Pull the LLM model if not already present; streams progress."""
    print(f"⏳ Pulling {LLM_MODEL} (skipped if already cached)…")
    resp = requests.post(
        f"{OLLAMA_HOST}/api/pull",
        json={"name": LLM_MODEL},
        stream=True,
        timeout=300,
    )
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            data = json.loads(line)
            status = data.get("status", "")
            if "pulling" in status or status == "success":
                print(f"  {status}")
            if status == "success":
                break
    print(f"✓ {LLM_MODEL} ready")


def llm_answer(query: str) -> str:
    """Generate an answer via Ollama. Used for both volatile and cache-miss queries."""
    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": f"Answer this question concisely in 1-2 sentences: {query}",
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


# ── Helpers ────────────────────────────────────────────────────────────────────

def embedding_literal(vec: list) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"


def get_cached(cur, emb_lit: str):
    """Call semantic_cache.get_cached_result(); return (result, similarity) or (None, None)."""
    cur.execute(
        """
        SELECT found, result_data, similarity_score
        FROM   semantic_cache.get_cached_result(
                   %s::text,
                   %s::float4,
                   NULL
               )
        """,
        (emb_lit, SIMILARITY_THRESHOLD),
    )
    row = cur.fetchone()
    if row and row["found"]:
        answer = row["result_data"]
        if isinstance(answer, str):
            try:
                answer = json.loads(answer)
            except json.JSONDecodeError:
                pass
        return str(answer), float(row["similarity_score"])
    return None, None


def store_cached(cur, query: str, emb_lit: str, result: str):
    """Call semantic_cache.cache_query() to persist the answer."""
    cur.execute(
        """
        SELECT semantic_cache.cache_query(
                   %s::text,
                   %s::text,
                   %s,
                   %s,
                   ARRAY[]::text[]
               )
        """,
        (query, emb_lit, Json(result), DEFAULT_TTL),
    )


# ── Main pipeline ──────────────────────────────────────────────────────────────

def process(conn, model, query: str):
    print(f"\n{'─'*68}")
    print(f"  Query   : {query!r}")

    # Step 1 — volatile gate (application layer, no DB or LLM touch yet)
    if is_volatile(query):
        print(f"  Decision: VOLATILE — calling LLM directly, skipping cache")
        t0 = time.time()
        result = llm_answer(query)
        elapsed = time.time() - t0
        with conn.cursor() as cur:
            cur.execute("UPDATE volatile_stats SET volatile_skipped = volatile_skipped + 1")
        conn.commit()
        print(f"  Result  : {result}  ({elapsed:.2f}s)")
        return

    # Step 2 — embed
    emb_lit = embedding_literal(model.encode(query).tolist())

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Step 3 — cache lookup via pg_semantic_cache
        cached, similarity = get_cached(cur, emb_lit)
        if cached is not None:
            conn.commit()
            print(f"  Decision: CACHE HIT  (similarity={similarity:.3f}) — LLM call saved")
            print(f"  Result  : {cached}")
            return
        conn.commit()

    # Step 4 — miss: call LLM then store
    print(f"  Decision: CACHE MISS — calling LLM…")
    t0 = time.time()
    result = llm_answer(query)
    elapsed = time.time() - t0

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        store_cached(cur, query, emb_lit, result)
    conn.commit()

    print(f"  Result  : {result}  ({elapsed:.2f}s, stored in cache)")


def print_stats(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM semantic_cache.cache_stats()")
        s = cur.fetchone()
        cur.execute("SELECT volatile_skipped FROM volatile_stats")
        skipped = cur.fetchone()["volatile_skipped"]

    total    = (s["total_hits"] or 0) + (s["total_misses"] or 0)
    hit_rate = s["total_hits"] / total * 100 if total else 0.0

    print(f"\n{'═'*68}")
    print("  CACHE STATISTICS")
    print(f"  {'Cache entries':<28}: {s['total_entries']}")
    print(f"  {'Cache hits':<28}: {s['total_hits']}")
    print(f"  {'Cache misses':<28}: {s['total_misses']}")
    print(f"  {'Volatile queries skipped':<28}: {skipped}")
    print(f"  {'Hit rate (non-volatile)':<28}: {hit_rate:.0f}%")
    print(f"{'═'*68}\n")


# ── Demo queries ───────────────────────────────────────────────────────────────

DEMO_QUERIES = [
    # Volatile — LLM called directly, cache never touched
    "What is the current time?",
    "What time is it right now?",
    "Tell me today's date.",
    "What's the current weather like?",
    "What is the current stock price of Apple?",

    # Non-volatile, first call → cache miss, LLM called, result stored
    "What is 2 + 2?",
    "What is the capital of France?",
    "What is the speed of light?",
    "Who created the Python programming language?",
    "What is the boiling point of water?",

    # Semantically similar rephrases → cache hit, LLM call saved
    "What does 2 plus 2 equal?",
    "What's the capital city of France?",
    "How fast does light travel?",
    "Who invented Python?",
    "At what temperature does water boil?",

    # Edge cases
    "What is 2+2?",                                    # near-exact → similarity ~1.0
    "What's today's live stock price of Apple?",       # volatile, different phrasing
]


def main():
    print("=" * 68)
    print("  pg_semantic_cache — Volatile Query Detection Demo")
    print("=" * 68)
    print()
    print("  Legend:")
    print("  VOLATILE   — time-sensitive; LLM called directly, cache bypassed")
    print("  CACHE MISS — not found; LLM called and answer stored in cache")
    print("  CACHE HIT  — semantically similar entry found; LLM call saved")

    # Load embedding model
    print("\n⏳ Loading embedding model (all-MiniLM-L6-v2)…")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("✓ Model ready")

    # Pull LLM model via Ollama
    pull_model()

    # Connect to PostgreSQL — retry while postgres is starting
    print("⏳ Connecting to PostgreSQL…")
    conn = None
    for attempt in range(15):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT,
                dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            )
            break
        except psycopg2.OperationalError:
            print(f"  Waiting for postgres… ({attempt + 1}/15)")
            time.sleep(3)
    if conn is None:
        raise RuntimeError("Could not connect to PostgreSQL after 15 attempts")
    print("✓ Connected to PostgreSQL\n")

    for query in DEMO_QUERIES:
        process(conn, model, query)

    print_stats(conn)
    conn.close()


if __name__ == "__main__":
    main()
