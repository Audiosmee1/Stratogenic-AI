import sys
import os
import streamlit as st


# ✅ Ensure Python finds 'app/' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prompt_library.short_descriptions import archetype_descriptions, expert_descriptions
from prompt_library.expert_prompts import EXPERT_CATEGORIES  # ✅ Now correctly imported
from app.cache_manager import get_cached_response, cache_response
from app.database import init_db_pool, log_user_query, get_recent_queries_with_responses
from app.plan_limits import PLAN_DETAILS
from app.user_queries import generate_response
from app.main import generate_summary


# ✅ Ensure database tables are created
init_db_pool()

# ✅ Initialize session state if not set
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_plan" not in st.session_state:
    st.session_state["user_plan"] = "The Foundation (Free)"
if "email" not in st.session_state:
    st.session_state["email"] = None
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "doc_usage_option" not in st.session_state:
    st.session_state["doc_usage_option"] = "Support AI Response"
doc_usage_option = st.session_state["doc_usage_option"]

# ✅ Streamlit UI
st.title("♟️ Stratogenic AI - AI-Driven Strategy Generator")

# ✅ Ensure `follow_up_query` is always defined
follow_up_query = ""

# ✅ Login Section (Ensure Login Comes First)
if "user_id" not in st.session_state or st.session_state["user_id"] is None:
    st.subheader("🔐 Login or Sign Up")

    email = st.text_input("📧 Email:")
    password = st.text_input("🔑 Password:", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            from app.user_management import authenticate_user  # ✅ Import only when needed

            user = authenticate_user(email, password)
            if user:
                st.session_state["user_id"] = user["user_id"]
                st.session_state["email"] = user["email"]  # ✅ Store Email in Session
                st.session_state["user_plan"] = user["plan"]

                # ✅ Check if user is an admin (Stored in Supabase)
                st.session_state["is_admin"] = user.get("is_admin", False)

                # ✅ Debugging (Print Admin Status)
                print(f"🛠 Admin Check: {st.session_state['email']} | Admin: {st.session_state['is_admin']}")

                st.success(f"✅ Logged in as {st.session_state['email']} ({st.session_state['user_plan']})")
                st.rerun()  # ✅ Refresh UI to apply changes
            else:
                st.error("❌ Invalid login. Try again.")

    with col2:
        if st.button("Sign Up"):
            from app.user_management import register_user  # ✅ Import register function

            success = register_user(email, password)
            if success:
                st.success("✅ Account created! Please log in.")
            else:
                st.error("❌ Registration failed. Try again.")

    # ✅ STOP EXECUTION TO PREVENT UI ELEMENTS BEFORE LOGIN

# ✅ Sidebar for User Plan & Admin Controls (Persists After Login)
st.sidebar.title("⚙️ Account Settings")

# ✅ Show Logged-In User with Correct Role
if st.session_state["user_id"]:
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False  # ✅ Ensure it always exists

    user_label = "👤 Standard User" if not st.session_state["is_admin"] else "🛠 Admin User"
    st.sidebar.subheader(f"{user_label}: {st.session_state['email']}")


    # ✅ Show Current Plan
    st.sidebar.subheader("📜 Your Plan:")
    current_plan = st.session_state["user_plan"]
    st.sidebar.write(f"**{current_plan}**")

    # ✅ Allow Admins to Change Plans for Themselves or Other Users
    if st.session_state["is_admin"]:
        st.sidebar.subheader("🛠 Admin: Change User Plan")
        plan_keys = list(PLAN_DETAILS.keys())

        # ✅ Ensure current_plan is valid, else default to "The Foundation (Free)"
        if current_plan not in plan_keys:
            print(f"⚠️ Plan '{current_plan}' not found in PLAN_DETAILS. Defaulting to 'The Foundation (Free)'.")
            current_plan = "The Foundation (Free)"

        new_plan = st.sidebar.selectbox("🔄 Select Plan", plan_keys,
                                        index=plan_keys.index(current_plan))

        if st.sidebar.button("🔄 Apply Plan Change"):
            from app.user_management import update_user_plan

            update_user_plan(st.session_state["email"], new_plan)  # ✅ Saves new plan in database
            st.session_state["user_plan"] = new_plan  # ✅ Updates UI instantly
            st.success(f"✅ Plan updated to {new_plan}!")
            st.rerun()  # ✅ Refresh UI

        if st.sidebar.button("🔄 Update Plan"):
            from app.user_management import update_user_plan

            update_user_plan(st.session_state["email"], new_plan)
            st.session_state["user_plan"] = new_plan
            st.success(f"✅ Plan updated to {new_plan}!")
            st.rerun()  # ✅ Refresh UI to apply changes

    # ✅ Display Plan Benefits
    st.sidebar.subheader("📊 Plan Benefits:")
    plan_details = PLAN_DETAILS[current_plan]
    st.sidebar.write(f"✅ **Queries per Month:** {PLAN_DETAILS[st.session_state['user_plan']]['queries']}")
    st.sidebar.write(f"✅ **Max Documents per Query:** {plan_details['documents']}")
    st.sidebar.write(f"✅ **Max Experts per Query:** {plan_details['max_experts']}")
    st.sidebar.write(f"✅ **Max Follow-Ups:** {PLAN_DETAILS[st.session_state['user_plan']]['follow_ups']}")
    st.sidebar.write(f"🤖 AI Model Used: {PLAN_DETAILS[st.session_state['user_plan']]['model']}")

    # ✅ Display Upgrade Option for Free Users
    if current_plan == "The Foundation (Free)":
        st.sidebar.warning("⚡ Upgrade to unlock more features!")

# ✅ Strategy Generation Section (ONLY after Login)
# ✅ Ensure user is logged in before showing query history
if "user_id" in st.session_state and st.session_state["user_id"]:
    user_id = st.session_state["user_id"]


    # ✅ Fetch recent queries & responses from the database
    recent_queries = get_recent_queries_with_responses(user_id)

    # ✅ Ensure user has selected a previous query before showing it
    selected_query = None
    selected_response = None

    # ✅ Dropdown to select a past query (Only show if queries exist)
    if recent_queries:
        formatted_queries = {
            f"{q[2].strftime('%Y-%m-%d %H:%M')} - {q[0][:50]}...": (q[0], q[1]) for q in recent_queries
        }
        selected_query_label = st.selectbox("🔍 Load a previous query:",
                                            ["Select a query..."] + list(formatted_queries.keys()))

        # ✅ Only assign selected query if the user actually picks one
        if selected_query_label != "Select a query...":
            selected_query, selected_response = formatted_queries[selected_query_label]

    # ✅ Display previous query & response ONLY if a query was selected
    if selected_query:
        st.text_area("Previous Query:", value=selected_query, height=150, key="loaded_query")
        st.text_area("Previous AI Response:", value=selected_response, height=68, key="loaded_response")

        if st.button("🔄 Reload This Query"):
            st.session_state["query"] = selected_query

            # ✅ Check if response is in Redis cache before making a new API call
            cached_response = get_cached_response(selected_query)
            if cached_response:
                st.session_state["response"] = cached_response
            else:
                st.session_state["response"] = selected_response  # Use stored DB response as fallback

            st.rerun()
    else:
        st.write("⚠️ No past queries found.")

if st.session_state["user_id"]:
    st.subheader("🧠 Generate Your AI Strategy")

    # ✅ Archetype Selection with Short Descriptions
    selected_archetype = st.selectbox(
        "🎭 Select an Archetype",
        options=[f"{archetype} - {desc}" for archetype, desc in archetype_descriptions.items()]
    )

    # ✅ Extract the Archetype Name Only (Removing the Description for Processing)
    selected_archetype = selected_archetype.split(" - ")[0]

    # ✅ Grouped Experts (Keeps Categories as Labels)
    grouped_experts = []
    expert_map = {}  # ✅ Keeps track of expert name mapping for later processing

    for category, experts in EXPERT_CATEGORIES.items():
        grouped_experts.append(f"🔹 {category} (Category)")  # ✅ Non-selectable label
        for expert in experts:
            # ✅ Fetch expert description from `expert_descriptions`, fallback if missing
            description = expert_descriptions.get(expert, "No description available")
            formatted_name = f"   ├── {expert} - {description}"  # ✅ Indented expert with description
            grouped_experts.append(formatted_name)
            expert_map[formatted_name] = expert  # ✅ Map formatted display to actual expert name

    # ✅ Allow Users to Select Any Experts (Total Limited by Plan)
    max_experts = PLAN_DETAILS[st.session_state["user_plan"]]["max_experts"]
    selected_experts_display = st.multiselect(
        f"🔍 Select Experts (Max: {max_experts} total)", grouped_experts, max_selections=max_experts
    )

    # ✅ Extract Clean Expert Names (Removing Indentation & Category Labels)
    selected_experts = [
        expert_map[display_name].split(" - ")[0] for display_name in selected_experts_display if
        not display_name.startswith("🔹")
    ]

    # ✅ Ensure selected experts are stored properly in session (Remove descriptions before processing)
    selected_experts = [
        expert.split(" - ")[0] for expert in selected_experts if not expert.startswith("🔹")
    ]

    if not selected_experts:
        st.warning("⚠ Please select at least one expert.")
    else:
        st.session_state["selected_experts"] = selected_experts

    # ✅ Document Upload UI
    max_documents = PLAN_DETAILS[st.session_state["user_plan"]]["documents"]
    uploaded_files = st.file_uploader(
        f"📂 Upload up to {PLAN_DETAILS[st.session_state['user_plan']]['documents']} documents (Max 10 pages each)",
        type=["pdf", "docx", "xlsx", "csv"],
        accept_multiple_files=True
    )

    # ✅ Show a warning for free/lower-tier users
    if max_documents == 1:
        st.warning(
            "⚠️ Multi-document analysis is a **premium feature**. Upgrade to a higher plan to analyze multiple documents together.")
    if uploaded_files and len(uploaded_files) > max_documents:
        st.error(
            f"❌ Your plan allows only {max_documents} document(s) per upload. Upgrade to a higher tier for multi-document analysis.")
        uploaded_files = uploaded_files[:max_documents]  # ✅ Restrict uploaded files to allowed limit
    # ✅ Upgrade Prompt for Free Users
    if max_documents == 1 and len(uploaded_files) == 1:
        if st.button("🚀 Upgrade to Unlock Multi-Document Analysis"):
            st.markdown("[Upgrade Now](https://your-upgrade-url.com)")  # ✅ Replace with actual upgrade link


    # ✅ Query Input

    # ✅ Define Query Disclaimer Modal State
    if "show_query_disclaimer" not in st.session_state:
        st.session_state["show_query_disclaimer"] = True  # ✅ Show it only on first query input

    # ✅ Show Query Disclaimer Before Allowing Input
    if st.session_state["show_query_disclaimer"]:
        with st.expander("🔍 Improve Your Query for Better AI Results!", expanded=True):
            st.write(
                "Your query **directly affects** the quality of the response. Here are some tips for best results:")
            st.markdown("""
            - ✅ **Be specific**: Instead of "How do I grow?", try "What are the best customer retention strategies for a SaaS company?"  
            - ✅ **Include relevant details**: AI performs better with **industry**, **target audience**, or **specific goals**.  
            - ❌ **Avoid vague requests**: "Tell me about business" → **This will produce a generic response.**  
            - ⚡ **Keep it clear and structured**: AI works best when queries are **concise** but **informative**.
            """)

            # ✅ Require Confirmation Before Proceeding
            if st.button("Got it! Proceed to Query Input"):
                st.session_state["show_query_disclaimer"] = False  # ✅ Hide the modal
                st.rerun()  # ✅ Refresh the UI

    query = ""  # ✅ Ensures `query` is always defined

    # ✅ Query Input Box (Now Appears Only After Confirmation)
    if not st.session_state["show_query_disclaimer"]:
        query = st.text_area("📝 Enter Your Query:",
                             placeholder="e.g., What are the best customer retention strategies for SaaS?")


    # ✅ Generate Insight Button
        def get_ai_response():
            return generate_response(
                user_id=st.session_state["user_id"],
                query=query,
                archetype=selected_archetype,
                selected_experts=selected_experts,
                uploaded_files=uploaded_files if uploaded_files else None,
                user_plan=st.session_state["user_plan"]
            )


        if st.button("🚀 Generate Insight"):
            if not query:
                st.warning("⚠ Please enter a query.")
            else:
                with st.spinner("✨ Generating AI-powered strategy..."):
                    cache_key = f"user_query:{st.session_state['user_id']}:{query}"
                    cached_response = get_cached_response(cache_key)

                    if cached_response:
                        full_report = cached_response  # ✅ Use cached response if available
                    else:
                        full_report = generate_response(
                            query=query,
                            user_id=st.session_state["user_id"],
                            archetype=selected_archetype,
                            selected_experts=selected_experts,  # ✅ Ensure experts are passed correctly
                            uploaded_files=uploaded_files if uploaded_files else None,
                            # ✅ Ensure document uploads are handled
                            user_plan=st.session_state["user_plan"]
                        )
                        cache_response(cache_key, full_report)  # ✅ Cache AI response

                    # ✅ Store full report in session for summary generation
                    st.session_state["full_report"] = full_report
                    st.session_state["initial_response"] = full_report  # ✅ Enables follow-ups

                    # ✅ Ensure follow-up count tracking is initialized correctly
                    if "follow_up_count" not in st.session_state:
                        st.session_state["follow_up_count"] = 0

                    # ✅ Log query only if it’s a new AI call (not from cache)
                    if not cached_response:
                        log_user_query(st.session_state["user_id"], query, full_report, st.session_state["user_plan"])

                    st.subheader("📜 AI Strategy Report")
                    st.write(full_report)

                    # ✅ Store full report in session for summary generation
                    st.session_state["full_report"] = full_report

                    # ✅ Store initial response to enable follow-ups
                    st.session_state["initial_response"] = full_report  # ✅ This enables follow-ups

                    # ✅ Initialize follow-up count if not set
                    if "follow_up_count" not in st.session_state:
                        st.session_state["follow_up_count"] = 0  # ✅ Ensures tracking starts

                        # ✅ Fix: Log the correct query and response (Fix: Replace follow_up_response)
                        log_user_query(st.session_state["user_id"], query, full_report, st.session_state["user_plan"])

        if st.button("📝 Generate Executive Summary"):
            with st.spinner("🔄 Summarizing AI Strategy Report..."):
                summary_report = generate_summary(st.session_state["full_report"], st.session_state["user_id"])
                st.subheader("📄 Executive Summary (AI-Generated)")
                st.write(summary_report)

    # ✅ Follow-Up Query Section (AFTER Report & Summary)
    if "initial_response" in st.session_state and st.session_state["initial_response"]:
        st.subheader("🔄 Follow-Up Query")
        follow_up_query = st.text_area("Enter your follow-up question:")

        # ✅ NEW: User selection for how documents should be used
        doc_usage_option = st.radio(
            "How should uploaded documents be used?",
            ["Support AI Response", "Summarize & Ask Direct Questions"],
            index=["Support AI Response", "Summarize & Ask Direct Questions"].index(
                st.session_state["doc_usage_option"])
        )

        st.session_state["doc_usage_option"] = doc_usage_option  # ✅ Ensure it persists

        # ✅ Ensure variables are initialized before they are used
        remaining_follow_ups = PLAN_DETAILS[st.session_state["user_plan"]]["follow_ups"]
        used_follow_ups = st.session_state.get("follow_up_count", 0)  # ✅ Ensures defined value

        if "follow_up_count" not in st.session_state:
            st.session_state["follow_up_count"] = 0

        used_follow_ups = st.session_state["follow_up_count"]  # ✅ Ensure tracking is accurate

        # ✅ Ensure `doc_usage_option` is always set (even if user hasn't selected anything)
        if "doc_usage_option" not in st.session_state:
            st.session_state["doc_usage_option"] = "Support AI Response"  # ✅ Set default value


        # ✅ Retrieve user selection if already made
        doc_usage_option = st.radio(
            "How should uploaded documents be used?",
            ["Support AI Response", "Summarize & Ask Direct Questions"],
            index=["Support AI Response", "Summarize & Ask Direct Questions"].index(
                st.session_state["doc_usage_option"]
            )
        )

    # ✅ Ensure follow-up tracking variables are always defined
    remaining_follow_ups = PLAN_DETAILS[st.session_state["user_plan"]]["follow_ups"]
    used_follow_ups = st.session_state.get("follow_up_count", 0)  # ✅ Ensures a defined value

    if st.button("Submit Follow-Up"):
        if not follow_up_query:
            st.warning("⚠ Please enter a follow-up question.")
            remaining_follow_ups = PLAN_DETAILS[st.session_state["user_plan"]]["follow_ups"]
            used_follow_ups = st.session_state.get("follow_up_count", 0)  # ✅ Ensures it always has a value

            st.warning("❌ You have reached your follow-up query limit. Upgrade your plan for more.")
        else:
            with st.spinner("🔄 Processing your follow-up..."):
                st.session_state["follow_up_response"] = generate_response(
                    user_id=st.session_state["user_id"],
                    query=follow_up_query,
                    archetype=selected_archetype,
                    selected_experts=selected_experts,
                    uploaded_files=None,
                    user_plan=st.session_state["user_plan"],
                    doc_usage_option=doc_usage_option  # ✅ No longer undefined
                )

                if st.session_state["follow_up_response"]:
                    st.session_state["follow_up_count"] = used_follow_ups + 1
                    st.subheader("📜 Follow-Up Response:")
                    st.write(st.session_state["follow_up_response"])

                    # ✅ Log the query & response at the same time
                    log_user_query(st.session_state["user_id"], follow_up_query,
                                   st.session_state["follow_up_response"],
                                   st.session_state["user_plan"])

