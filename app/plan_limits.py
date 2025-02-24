import redis
import os
from app.one_time_access import check_one_time_access  # ✅ Import one-time access check
from app.config import PLAN_DETAILS  # ✅ Import from centralized config file
from app.user_management import is_admin  # ✅ Import Admin Check

# Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def check_usage_limit(user_id, user_plan, service_type):
    """Checks if the user has exceeded their plan's limit OR if they have one-time Enterprise access."""

    # ✅ First, bypass limits if user is Admin
    admin_status = is_admin(user_id)
    print(f"🔍 Checking Admin Status - User ID: {user_id}, Is Admin: {admin_status}")

    if admin_status:
        print(f"✅ Admin Bypass Applied for User ID: {user_id}")
        return True  # ✅ Admins have unlimited access

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

def check_pdf_limit(user_id, user_plan):
    """Ensures users don't exceed their strategy PDF generation limit."""
    allowed_pdfs = PLAN_DETAILS[user_plan]["strategy_pdfs"]
    generated_pdfs = int(redis_client.get(f"user_pdfs:{user_id}") or 0)

    if generated_pdfs >= allowed_pdfs:
        return False  # ✅ Limit exceeded
    redis_client.incr(f"user_pdfs:{user_id}")
    return True


def check_document_limit(user_id, user_plan):
    """Enforces fair use limit for document uploads."""
    allowed_docs = PLAN_DETAILS[user_plan]["documents"]
    uploaded_docs = int(redis_client.get(f"user_docs_uploaded:{user_id}") or 0)

    if uploaded_docs >= allowed_docs:
        return False  # Limit exceeded
    return True

def reset_all_user_limits():
    """Resets query, follow-up, and document usage for all users."""
    keys_to_reset = ["user_queries_count", "user_follow_ups_count", "user_docs_uploaded"]

    # Get all user IDs
    user_keys = redis_client.keys("user_queries_count:*")

    for key in user_keys:
        user_id = key.split(":")[-1]  # Extract user ID
        for prefix in keys_to_reset:
            redis_client.set(f"{prefix}:{user_id}", 0)  # Reset usage

    print("✅ Reset all user limits successfully.")
