# Integration Examples

This page provides integration examples for using pg_semantic_cache with
popular programming languages and embedding providers.

## Python with OpenAI

The following example demonstrates how to integrate the semantic cache with
OpenAI embeddings using Python and the psycopg2 library.

In the following example, the `SemanticCache` class wraps the cache functions
and handles embedding generation through the OpenAI API.

```python
import psycopg2
import openai
import json
from typing import Optional, Dict, Any

class SemanticCache:
    """Semantic cache wrapper for PostgreSQL"""

    def __init__(self, conn_string: str, openai_api_key: str):
        self.conn = psycopg2.connect(conn_string)
        self.client = openai.OpenAI(api_key=openai_api_key)

    def _get_embedding(self, text: str) -> str:
        """Generate embedding using OpenAI"""
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        return f"[{','.join(map(str, embedding))}]"

    def cache(self, query: str, result: Dict[Any, Any],
              ttl: int = 3600, tags: Optional[list] = None) -> int:
        """Cache a query result"""
        embedding = self._get_embedding(query)

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT semantic_cache.cache_query(
                    %s::text, %s::text, %s::jsonb, %s::int, %s::text[]
                )
            """, (query, embedding, json.dumps(result), ttl, tags))
            cache_id = cur.fetchone()[0]
            self.conn.commit()
            return cache_id

    def get(self, query: str, similarity: float = 0.95,
            max_age: Optional[int] = None) -> Optional[Dict[Any, Any]]:
        """Retrieve from cache"""
        embedding = self._get_embedding(query)

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT found, result_data, similarity_score, age_seconds
                FROM semantic_cache.get_cached_result(
                    %s::text, %s::float4, %s::int
                )
            """, (embedding, similarity, max_age))

            result = cur.fetchone()
            if result and result[0]:  # Cache hit
                print(f"Cache HIT (similarity: {result[2]:.3f}, age: {result[3]}s)")
                return json.loads(result[1])
            else:
                print("Cache MISS")
                return None

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM semantic_cache.cache_stats()")
            columns = [desc[0] for desc in cur.description]
            values = cur.fetchone()
            return dict(zip(columns, values))

# Usage example
cache = SemanticCache(
    conn_string="dbname=mydb user=postgres",
    openai_api_key="sk-..."
)

# Try to get from cache, compute if miss
def get_revenue_data(query: str) -> Dict:
    result = cache.get(query, similarity=0.95)

    if result:
        return result  # Cache hit!

    # Cache miss - compute the result
    result = expensive_database_query()  # Your expensive query here
    cache.cache(query, result, ttl=3600, tags=['revenue', 'analytics'])
    return result

# Example queries
data1 = get_revenue_data("What was Q4 2024 revenue?")
data2 = get_revenue_data("Show me revenue for last quarter")
data3 = get_revenue_data("Q4 sales figures?")

# View statistics
print(cache.stats())
```

The preceding example demonstrates three key operations:

- The cache initialization with database connection and API credentials.
- The automatic fallback from cache lookup to computation when needed.
- The statistical monitoring to track cache performance over time.

## Node.js with OpenAI

The following example shows how to use the semantic cache with Node.js and
the OpenAI API through an asynchronous interface.

In the following example, the `SemanticCache` class uses async/await patterns
to handle database operations and embedding generation.

```javascript
const { Client } = require('pg');
const OpenAI = require('openai');

class SemanticCache {
    constructor(pgConfig, openaiApiKey) {
        this.client = new Client(pgConfig);
        this.openai = new OpenAI({ apiKey: openaiApiKey });
        this.client.connect();
    }

    async getEmbedding(text) {
        const response = await this.openai.embeddings.create({
            model: 'text-embedding-ada-002',
            input: text
        });
        const embedding = response.data[0].embedding;
        return `[${embedding.join(',')}]`;
    }

    async cache(query, result, ttl = 3600, tags = null) {
        const embedding = await this.getEmbedding(query);
        const res = await this.client.query(
            `SELECT semantic_cache.cache_query($1::text, $2::text, $3::jsonb, $4::int, $5::text[])`,
            [query, embedding, JSON.stringify(result), ttl, tags]
        );
        return res.rows[0].cache_query;
    }

    async get(query, similarity = 0.95, maxAge = null) {
        const embedding = await this.getEmbedding(query);
        const res = await this.client.query(
            `SELECT * FROM semantic_cache.get_cached_result($1::text, $2::float4, $3::int)`,
            [embedding, similarity, maxAge]
        );

        const { found, result_data, similarity_score, age_seconds } = res.rows[0];

        if (found) {
            console.log(`Cache HIT (similarity: ${similarity_score.toFixed(3)}, age: ${age_seconds}s)`);
            return JSON.parse(result_data);
        } else {
            console.log('Cache MISS');
            return null;
        }
    }

    async stats() {
        const res = await this.client.query('SELECT * FROM semantic_cache.cache_stats()');
        return res.rows[0];
    }
}

// Usage
const cache = new SemanticCache(
    { host: 'localhost', database: 'mydb', user: 'postgres' },
    'sk-...'
);

async function getRevenueData(query) {
    const cached = await cache.get(query);
    if (cached) return cached;

    const result = await expensiveDatabaseQuery();
    await cache.cache(query, result, 3600, ['revenue', 'analytics']);
    return result;
}
```

## Additional Resources

The repository includes additional integration examples and test files.

For more comprehensive examples, refer to the following files:

- The `examples/usage_examples.sql` file contains comprehensive SQL examples.
- The `test/benchmark.sql` file provides performance testing examples.
