import sys
import os
import openai  # ✅ Ensure OpenAI is only used here
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Set API key
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("❌ OpenAI API key is missing. Ensure it's set in the `.env` file.")
print(f"✅ OpenAI API Key Loaded: {openai.api_key[:5]}********")  # ✅ Debugging (only show first 5 characters)

# ✅ Ensure Python finds 'app/' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import PLAN_DETAILS
from app.document_processing import extract_text, pre_screen_documents, analyze_patterns  # ✅ Only relevant imports
from prompt_library.expert_prompts import expert_prompts
from prompt_library.archetype_prompts import archetype_prompts
from app.cache_manager import get_cached_response, cache_response
from app.database import log_user_query

def process_user_request(user_id, query, archetype, selected_experts, uploaded_files, user_plan,doc_usage_option=None):
    """
    Processes user request, integrates expert guidance, document analysis, and calls OpenAI.
    """
    # ✅ First, check Redis cache before making an API call
    cache_key = f"user_query:{user_id}:{archetype}:{query}"
    cached_response = get_cached_response(cache_key)

    if cached_response:
        return cached_response  # ✅ Use cached response if available

    # ✅ Log the user's query before AI processing
    log_user_query(user_id, query, None, user_plan, archetype)

    expert_prompt = f"📌 **How {archetype} Uses Expert Insights:**\n"
    expert_prompt += archetype_prompts.get(archetype + "_experts", "Your experts serve as strategic advisors.") + "\n\n"
    expert_prompt += "\n".join(
        [f"🔹 **{expert}** → {expert_prompts.get(expert, 'Key insights tailored to this strategy.')}" for expert in
         selected_experts]
    )

    # ✅ Document Processing
    if uploaded_files:
        extracted_texts = extract_text(uploaded_files)

        if doc_usage_option == "Summarize & Ask Direct Questions":
            formatted_docs = "\n".join([f"📄 {name}: {text[:500]}" for name, text in extracted_texts.items()])
        else:
            formatted_docs = "\n".join([f"📄 {name}: {text}" for name, text in extracted_texts.items()])
    else:
        extracted_texts = {}
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
    🎭 **{archetype} Strategic Thinking Model**
    📌 {archetype_prompts.get(archetype, 'Default archetypal approach.')}

    🛠 **Key Strengths of {archetype} Strategy:**
    - {archetype_prompts.get(archetype + '_strengths', 'Adaptive execution and high-impact decision-making.')}
    - {archetype_prompts.get(archetype + '_priority', 'Scalability, competitive positioning, and risk management.')}

    📌 **AI Directive:** Responses must align with {archetype}'s leadership principles.

    🎓 **Expert Contributions (Aligned with {archetype} Thinking):**
    {expert_prompt}

    📂 **Document Insights (Analyzed Through the {archetype} Lens):**
    {formatted_docs if formatted_docs else 'No additional documents provided.'}

    📝 **User Query (Framed Within {archetype} Reasoning):**
    "{query}"

    📊 **Strategic Depth:**  
    {report_depth}
    """

    # ✅ Call OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo" if user_plan != "Free" else "gpt-3.5-turbo",
        messages=[{"role": "system", "content": structured_query}],
        max_tokens=2000
    )

    print(f"✅ Processing Query - User: {user_id}, Archetype: {archetype}, Query: {query}")

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
