import redis
import json

# ✅ Explicitly force Redis into synchronous mode
redis_pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=True)
redis_client = redis.Redis(connection_pool=redis_pool)


def store_user_session(user_id, session_data, expiration=3600):
    """Stores user session data in Redis for 1 hour (default)."""
    session_data_str = json.dumps(session_data)  # ✅ Convert to JSON string
    redis_client.setex(f"user_session:{user_id}", expiration, session_data_str)


def get_user_session(user_id):
    """Retrieves stored user session data safely."""
    session_data = redis_client.get(f"user_session:{user_id}")
    if session_data:
        try:
            return json.loads(str(session_data))  # ✅ Ensure proper string handling
        except json.JSONDecodeError:
            return None
    return None


def store_ai_memory(user_id, query, response, expiration=86400):
    """Stores AI memory (query-response pairs) in Redis for 24 hours."""
    ai_data = json.dumps({"query": query, "response": response})
    redis_client.setex(f"ai_memory:{user_id}", expiration, ai_data)

    # ✅ Track total user queries
    redis_client.incr(f"user_query_count:{user_id}")

    # ✅ Track follow-ups separately
    if "follow-up" in query.lower():
        redis_client.incr(f"user_follow_up_count:{user_id}")


def get_ai_memory(user_id):
    """Retrieves stored AI memory for continuity in follow-ups."""
    memory_data = redis_client.get(f"ai_memory:{user_id}")
    if memory_data:
        try:
            return json.loads(str(memory_data))  # ✅ Force correct type conversion
        except json.JSONDecodeError:
            redis_client.delete(f"ai_memory:{user_id}")  # Remove corrupted data
    return None


# ✅ Track User Query Counts
def track_query_count(user_id):
    """Increments the query count for a user."""
    redis_client.incr(f"user_query_count:{user_id}")


def get_user_query_count(user_id):
    """Retrieves the number of queries a user has made."""
    count = redis_client.get(f"user_query_count:{user_id}")
    return int(count) if count and count.isdigit() else 0  # ✅ Convert to int safely


# ✅ Track Follow-Up Query Counts
def track_follow_up_count(user_id):
    """Increments the follow-up query count for a user."""
    redis_client.incr(f"user_follow_up_count:{user_id}")


def get_user_follow_up_count(user_id):
    """Retrieves the number of follow-ups a user has made."""
    count = redis_client.get(f"user_follow_up_count:{user_id}")
    return int(count) if count and count.isdigit() else 0  # ✅ Convert to int safely


# ✅ Cache API Responses
def cache_response(query, response, expiration=86400):
    """Stores query responses in Redis for a set expiration (default: 24 hours)."""
    redis_client.setex(f"query_cache:{query}", expiration, str(response))  # ✅ Ensure string type


def get_cached_response(query):
    """Retrieves cached response from Redis, if available."""
    cached_response = redis_client.get(f"query_cache:{query}")
    return str(cached_response) if cached_response else ""  # ✅ Ensure proper type


# ✅ Clear Expired Cache Entries
def clear_old_cache_entries():
    """Removes expired cache keys from Redis to prevent excessive storage."""
    query_keys = redis_client.keys("query_cache:*")
    for key in query_keys:
        if redis_client.ttl(key) == -1:  # ✅ Check if TTL has expired
            redis_client.delete(key)


# ✅ Track Query Frequency
def track_query_frequency(query):
    """Tracks how often a query is asked."""
    redis_client.incr(f"query_count:{query}")


def get_frequent_queries(top_n=5):
    """Retrieves the most frequently asked queries from Redis."""
    query_keys = redis_client.keys("query_count:*")
    query_counts = {key: int(redis_client.get(key) or 0) for key in query_keys}
    sorted_queries = sorted(query_counts, key=query_counts.get, reverse=True)[:top_n]
    return [query.replace("query_count:", "") for query in sorted_queries]
