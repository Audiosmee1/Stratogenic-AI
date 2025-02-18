import sys
import os
import openai  # ✅ Ensure OpenAI is only used here

# ✅ Ensure Python finds 'app/' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import PLAN_DETAILS
from app.document_processing import extract_text, pre_screen_documents, analyze_patterns  # ✅ Only relevant imports
from prompt_library.expert_prompts import expert_prompts
from prompt_library.archetype_prompts import archetype_prompts
from app.cache_manager import get_cached_response, cache_response
from app.database import log_user_query

def process_user_request(user_id, query, archetype, selected_experts, uploaded_files, user_plan):
    """
    Processes user request, integrates expert guidance, document analysis, and calls OpenAI.
    """
    # ✅ First, check Redis cache before making an API call
    cache_key = f"user_query:{user_id}:{query}"
    cached_response = get_cached_response(cache_key)

    if cached_response:
        return cached_response  # ✅ Use cached response if available

    # ✅ Log the user's query before AI processing
    log_user_query(user_id, query, None, user_plan)

    # ✅ Fetch Expert Guidance
    expert_prompt = "\n".join(
        [f"- **{expert}**: {expert_prompts.get(expert, 'No specific guidance.')}" for expert in selected_experts]
    ) if selected_experts else "No specific expert input selected."

    # ✅ Document Processing
    extracted_texts = extract_text(uploaded_files) if uploaded_files else {}
    formatted_docs = "📂 No additional documents provided." if not extracted_texts else ""

    # ✅ Ensure only valid documents are processed
    valid_texts = {name: text for name, text in extracted_texts.items() if "Error extracting" not in text}

    if valid_texts:  # ✅ Only process if `valid_texts` is not empty
        if len(valid_texts) >= 3:
            pre_screen_results = pre_screen_documents(valid_texts)

            # ✅ Only Run Pattern Analysis if Docs Are Compatible
            if "not related" in pre_screen_results.lower():
                formatted_docs = f"⚠️ AI detected these documents are **not related.** Proceed with caution.\n\n{pre_screen_results}"
            else:
                pattern_analysis = analyze_patterns(valid_texts)
                formatted_docs = f"📂 **AI-Detected Patterns Across Documents:**\n{pattern_analysis}"
        else:
            formatted_docs = "\n".join([f"📄 {name}: {text[:1000]}" for name, text in valid_texts.items()])

    # ✅ Fetch Report Depth Based on User Plan
    report_depth = PLAN_DETAILS.get(user_plan, {}).get("report_depth", """
    🚀 **Generate a structured response that includes:**
    1️⃣ **Summary of key insights**
    2️⃣ **Three actionable steps**
    3️⃣ **One major risk to consider**
    """)
    summary_available = PLAN_DETAILS.get(user_plan, {}).get("summary_available", False)

    # ✅ Format the Query Before Sending to AI
    structured_query = f"""
    🎭 **Archetypal Strategy Tone:** {archetype_prompts.get(archetype, 'Default tone')}

    🎓 **Expert Contributions:**  
    {expert_prompt}

    📂 **Documents (if any):**  
    {formatted_docs if formatted_docs else 'No additional documents provided.'}

    📝 **User Query:**  
    "{query}"

    {report_depth}  # ✅ Now pulled dynamically from PLAN_DETAILS
    """

    # ✅ Call OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo" if user_plan != "Free" else "gpt-3.5-turbo",
        messages=[{"role": "system", "content": structured_query}],
        max_tokens=2000
    )

    ai_response = response.choices[0].message["content"]  # ✅ Returns AI-generated response

    # ✅ If Summary is Available, Generate One Using AI
    if summary_available:
        summary_prompt = f"Summarize this report in ~300 words:\n\n{ai_response}"
        summary_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": summary_prompt}],
            max_tokens=500
        ).choices[0].message["content"]
        return ai_response, summary_response  # ✅ Return both full report & summary

    return ai_response


def generate_summary(full_report, user_id):
    """
    Summarizes a business strategy report using AI while keeping follow-up memory.
    """
    # ✅ Check Redis cache first
    cache_key = f"summary:{user_id}"
    cached_summary = get_cached_response(cache_key)

    if cached_summary:
        return cached_summary  # ✅ Use cached summary if available

    summary_prompt = f"Summarize this business strategy report in a concise and actionable way:\n\n{full_report}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": summary_prompt}],
        max_tokens=500
    )

    return response.choices[0].message["content"]
