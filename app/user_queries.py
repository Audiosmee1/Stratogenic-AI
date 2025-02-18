import re
from app.main import process_user_request
from app.user_management import check_one_time_access
from app.config import PLAN_DETAILS
from app.cache_manager import get_cached_response, cache_response, track_query_count, track_follow_up_count, get_user_query_count, get_user_follow_up_count

def check_usage_limit(user_id, user_plan, usage_type):
    """Checks if the user has exceeded their plan's limit OR if they have one-time Enterprise access."""
    if user_plan == "One-Time Enterprise Report (£25)":
        return check_one_time_access(user_id) > 0

    if usage_type == "queries":
        usage_count = get_user_query_count(user_id)
        max_queries = PLAN_DETAILS[user_plan]["queries"]
        return usage_count < max_queries  # ✅ Ensure user stays within limits

    if usage_type == "follow_ups":
        follow_up_count = get_user_follow_up_count(user_id)
        max_follow_ups = PLAN_DETAILS[user_plan]["follow_ups"]
        return follow_up_count < max_follow_ups  # ✅ Ensure follow-up limits are respected

    return True  # ✅ If no limit applies, allow request

def preprocess_query(query):
    """Trims unnecessary words from user queries while keeping meaning intact."""
    query = query.strip()
    query = re.sub(r'\b(hey|hi|please|thanks|wondering|could you help me with|can you tell me)\b', '', query,
                   flags=re.IGNORECASE)
    query = re.sub(r'\s+', ' ', query).strip()
    return query.capitalize()

def generate_response(query, user_id, archetype, selected_experts, user_plan, uploaded_files=None,
                          doc_usage_option=None):
    """
    Prepares the structured query, checks Redis, and forwards it to main.py for AI processing.
    """
    cache_key = f"user_query:{user_id}:{query}"
    cached_response = get_cached_response(cache_key)

    if cached_response:
        return cached_response  # ✅ Use cached response if available

    # ✅ Ensure user has not exceeded their allowed query usage
    if not check_usage_limit(user_id, user_plan, "queries"):
        return "❌ Query limit reached. Upgrade your plan for more."

    # ✅ Track query usage in Redis
    track_query_count(user_id)

    # ✅ Forward request to main.py for AI processing
    structured_query = {
        "user_id": user_id,
        "query": query,
        "archetype": archetype,
        "selected_experts": selected_experts,
        "uploaded_files": uploaded_files,
        "user_plan": user_plan,
        "doc_usage_option": doc_usage_option  # ✅ Now explicitly passed
    }

    ai_response = process_user_request(**structured_query)

    # ✅ Cache AI response for future reuse
    cache_response(cache_key, ai_response)

    return ai_response

def generate_follow_up_response(query, user_id, archetype, user_plan):
    """
    Handles follow-up queries, ensuring they check Redis first and enforce limits.
    """
    cache_key = f"follow_up:{user_id}:{query}"
    cached_follow_up = get_cached_response(cache_key)

    if cached_follow_up:
        return cached_follow_up  # ✅ Use cached response if available

    # ✅ Ensure user has not exceeded their allowed follow-up usage
    if not check_usage_limit(user_id, user_plan, "follow_ups"):
        return "❌ Follow-up limit reached. Upgrade your plan for more."

    # ✅ Track follow-up usage in Redis
    track_follow_up_count(user_id)

    # ✅ Process follow-up query
    structured_query = {
        "user_id": user_id,
        "query": query,
        "archetype": archetype,
        "selected_experts": [],  # ✅ Experts are only assigned in the initial query
        "uploaded_files": None,
        "user_plan": user_plan
    }

    ai_follow_up_response = process_user_request(**structured_query)

    # ✅ Cache follow-up response
    cache_response(cache_key, ai_follow_up_response)

    return ai_follow_up_response
