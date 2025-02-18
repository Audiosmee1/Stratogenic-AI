import redis
import os
from app.one_time_access import check_one_time_access  # ✅ Import one-time access check
from app.config import PLAN_DETAILS  # ✅ Import from centralized config file

# Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def check_usage_limit(user_id, user_plan, service_type):
    """Checks if the user has exceeded their plan's limit OR if they have one-time Enterprise access."""

    # ✅ Handle invalid user plans gracefully
    if user_plan not in PLAN_DETAILS:
        print(f"❌ Invalid user plan: {user_plan}")
        return False  # Prevent crashes from unknown plans

    # ✅ One-time purchase check
    if user_plan == "One-Time Enterprise Report":
        if service_type == "follow_ups":
            return check_one_time_access(user_id) > 0  # ✅ Return True if follow-ups remain
        elif service_type == "queries":
            query_count = int(redis_client.get(f"user_{service_type}_count:{user_id}") or 0)
            if query_count >= 1:
                return False  # ✅ Prevent second query
            redis_client.incr(f"user_{service_type}_count:{user_id}")  # ✅ Now it properly tracks the query count
            return True

    # ✅ Normal plan-based limits
    user_limit = PLAN_DETAILS[user_plan].get(service_type)

    if user_limit == "Unlimited":
        return True  # No restriction for paid users with unlimited plans

    usage_count = int(redis_client.get(f"user_{service_type}_count:{user_id}") or 0)

    if usage_count >= user_limit:
        return False  # User has exceeded the limit

    redis_client.incr(f"user_{service_type}_count:{user_id}")  # ✅ Increment usage count
    return True

def check_document_limit(user_id, user_plan):
    """Enforces fair use limit for document uploads."""
    allowed_docs = PLAN_DETAILS[user_plan]["documents"]
    uploaded_docs = int(redis_client.get(f"user_docs_uploaded:{user_id}") or 0)

    if uploaded_docs >= allowed_docs:
        return False  # Limit exceeded
    return True

