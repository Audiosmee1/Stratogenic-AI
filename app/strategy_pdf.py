import os
import openai
import pdfkit
from app.database import get_db_connection, release_db_connection
from app.cache_manager import cache_response, get_cached_response
from prompt_library.archetype_prompts import archetype_prompts
from prompt_library.expert_prompts import expert_prompts

def generate_strategy_pdf(user_id, structured_inputs, archetype, selected_experts):
    """Generates a structured AI-driven strategy report and converts it into a PDF."""

    # ✅ Extract structured user inputs
    industry = structured_inputs.get("industry", "").strip()

    if not industry or industry.lower() == "other":
        industry = "No specific industry provided. Use general best practices."
    goal = structured_inputs.get("goal", "General strategy")
    revenue_model = structured_inputs.get("revenue_model", "N/A")
    competitors = structured_inputs.get("competitors", "").strip()
    if not competitors:
        competitors = "No specific competitors provided. Analyze general industry competition instead."

    # ✅ Retrieve Archetypal Strategy Tone
    archetype_tone = archetype_prompts.get(archetype, "No specific archetypal guidance.")

    # ✅ Fetch Expert Insights
    expert_insights = "\n".join(
        [f"- **{expert}**: {expert_prompts.get(expert, 'No specific guidance.')}" for expert in selected_experts]
    ) if selected_experts else "No expert insights selected."

    # ✅ Create AI prompt
    ai_prompt = f"""
    🎯 **AI-Generated Business Strategy Report**  
    🏛 **Unique Selling Proposition:** Stratogenic AI provides **expert-backed, archetypally driven strategies** that align with the user's specific business model.  

    📍 **Industry:** {industry if industry != 'No specific industry provided.' else "Provide strategic insights applicable across multiple sectors."}
    🎯 **Strategy Goal:** {goal}  
    💰 **Revenue Model:** {revenue_model}  
    🏆 **Competitor Analysis:** 
    {competitors if competitors != 'No specific competitors provided.' else "Provide a market overview based on industry trends and common competitive strategies."}

    🎭 **{archetype}: Your Strategy Blueprint**
    📌 **Strategic Thinking Model:** {archetype_tone} 
    🛠 **Key Strengths of This Approach:**
    - {archetype_prompts.get(archetype + "_strengths", "Focused execution and high-impact decision-making.")}
    - {archetype_prompts.get(archetype + "_priority", "Rapid scalability and risk management.")}

    🎓 **Expert Insights (Aligned with {archetype} Thinking):**
    {expert_insights}


    🎓 **Expert Insights:**  
    {expert_insights}  

    📜 **Strategic Plan Breakdown:**  
    1️⃣ **Executive Summary**  
       - High-level strategy overview tailored to {industry} business growth.  
    2️⃣ **Step-by-Step Execution Plan** (5-10 key actions)  
    3️⃣ **Risk Assessment & Mitigation**  
    4️⃣ **Scaling & Growth Strategies**  
    5️⃣ **Competitive Positioning Recommendations**  
    6️⃣ **Financial & Investment Considerations**  
    7️⃣ **Final Recommendations & Next Steps**  
    """

    # ✅ Check cache first to avoid redundant API calls
    cache_key = f"strategy_pdf:{user_id}:{goal}"
    cached_response = get_cached_response(cache_key)

    if cached_response:
        strategy_content = cached_response
    else:
        # ✅ Call OpenAI API to generate structured strategy
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": ai_prompt}],
            max_tokens=3000
        )
        strategy_content = response.choices[0].message["content"]
        cache_response(cache_key, strategy_content)

    # ✅ Convert AI response to PDF format
    pdf_filename = f"strategy_report_{user_id}.pdf"
    pdfkit.from_string(strategy_content, pdf_filename)

    # ✅ Store PDF in DB for retrieval
    store_generated_pdf(user_id, pdf_filename)

    return pdf_filename

def store_generated_pdf(user_id, pdf_filename):
    """Stores generated strategy reports in the database for user retrieval."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO strategy_reports (user_id, pdf_filename, created_at)
            VALUES (%s, %s, NOW());
        """, (user_id, pdf_filename))
        conn.commit()
    except Exception as e:
        print(f"❌ Failed to store PDF: {e}")
    finally:
        release_db_connection(conn)

def get_user_reports(user_id):
    """Retrieves previously generated strategy reports for a user."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT pdf_filename, created_at FROM strategy_reports WHERE user_id = %s ORDER BY created_at DESC;", (user_id,))
        reports = cursor.fetchall()
        return reports  # Returns a list of (pdf_filename, timestamp)
    except Exception as e:
        print(f"❌ Failed to fetch reports: {e}")
        return []
    finally:
        release_db_connection(conn)
