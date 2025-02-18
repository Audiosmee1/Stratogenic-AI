import schedule
import time
from app.cache_manager import get_frequent_queries, cache_response, get_cached_response  # ✅ Add get_cached_response
from app.user_queries import generate_response

def batch_cache_frequent_queries():
    """Caches responses for the most frequently asked queries to reduce API load."""
    frequent_queries = get_frequent_queries(top_n=5)
    cached_queries = []

    for query in frequent_queries:
        if not get_cached_response(query):
            print(f"⏳ Caching response for: {query}")
            response = generate_response(query, user_id="system")  # ✅ Assign a default user_id
            cache_response(query, response, expiration=259200)
            cached_queries.append(query)

    print(f"✅ Batch cache updated. Cached Queries: {', '.join(cached_queries) if cached_queries else 'None'}")

def start_scheduler():
    """Starts the scheduler to run batch cache updates daily at 3 AM."""
    print("✅ Scheduler started. Running batch cache updates daily at 3 AM.")
    schedule.every().day.at("03:00").do(batch_cache_frequent_queries)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every 60 seconds

if __name__ == "__main__":
    start_scheduler()
