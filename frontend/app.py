import sys
import os
import streamlit as st


# ✅ Ensure Python finds 'app/' directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prompt_library.archetype_prompts import archetype_prompts  # ✅ Import archetype prompts
from prompt_library.expert_prompts import expert_prompts  # ✅ Import expert prompts
from app.strategy_pdf import generate_strategy_pdf  # ✅ Import the strategy PDF generation function

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
# ✅ Ensure session state variables are initialized
if "query_submitted" not in st.session_state:
    st.session_state["query_submitted"] = False  # ✅ Default value
if "selected_archetype" not in st.session_state:
    st.session_state["selected_archetype"] = None  # ✅ Default to None
if "selected_experts" not in st.session_state:
    st.session_state["selected_experts"] = []  # ✅ Default empty list
if "doc_usage_option" not in st.session_state:
    st.session_state["doc_usage_option"] = "Support AI Response"
if "selected_experts_tab1" not in st.session_state:
    st.session_state["selected_experts_tab1"] = []  # ✅ Default to an empty list
if "selected_experts_tab2" not in st.session_state:
    st.session_state["selected_experts_tab2"] = []  # ✅ Default to an empty list

doc_usage_option = st.session_state["doc_usage_option"]

# ✅ Set path to the logo image
logo_path = os.path.join(os.path.dirname(__file__), "assets", "Statogenic AI.png")

# ✅ Display the logo
st.image(logo_path, use_container_width=True)

# ✅ Streamlit UI
st.title("Stratogenic AI - AI-Driven Strategy Generator")

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
    # ✅ Create Tabs for AI Strategy & PDF Strategy Report
    tab1, tab2 = st.tabs(["🧠 AI Insight Generator", "📜 Structured Strategy Report"])

    # ✅ Tab 1: AI Strategy Generator
    with tab1:
        if st.session_state["user_id"]:
            st.subheader("🧠 Define Your Focus")

        # ✅ Ensure Archetype is Stored in Session State for Tab 1
        if "selected_archetype_tab1" not in st.session_state:
            st.session_state["selected_archetype_tab1"] = list(archetype_descriptions.keys())[
                0]  # Default to first archetype

        selected_archetype = st.selectbox(
            "🎭 Select an Archetype",
            options=[f"{archetype} - {desc}" for archetype, desc in archetype_descriptions.items()],
            index=list(archetype_descriptions.keys()).index(st.session_state["selected_archetype_tab1"])
        )

        st.session_state["selected_archetype_tab1"] = selected_archetype.split(" - ")[0]  # ✅ Remove description

        # ✅ Ensure `selected_experts_tab1` is initialized before using it
        if "selected_experts_tab1" not in st.session_state:
            st.session_state["selected_experts_tab1"] = []  # ✅ Default to an empty list

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

        # ✅ Create multiselect widget WITHOUT modifying session state afterward
        selected_experts_display_tab1 = st.multiselect(
            f"🔍 Select Experts (Max: {max_experts} total)",
            options=grouped_experts,
            default=st.session_state.get("selected_experts_tab1", []),  # ✅ Use `.get()` to avoid KeyError
            max_selections=max_experts,
            key="selected_experts_tab1"
        )

        # ✅ Extract Clean Expert Names (Removing Indentation & Category Labels)
        selected_experts = [
            expert_map[display_name].split(" - ")[0] for display_name in selected_experts_display_tab1 if
            not display_name.startswith("🔹")
        ]

        if "selected_experts_tab1" not in st.session_state:
            st.session_state["selected_experts_tab1"] = []  # ✅ Default to an empty list
        elif set(selected_experts_tab1) != set(st.session_state["selected_experts_tab1"]):
            st.session_state["selected_experts_tab1"] = selected_experts_tab1  # ✅ Update only when needed

        # ✅ Ensure at least one expert is selected (correctly checking the extracted expert list)
        if len(selected_experts) == 0:
            st.warning("⚠ Please select at least one expert.")

        # ✅ Document Upload UI
        max_documents = PLAN_DETAILS[st.session_state["user_plan"]]["documents"]
        uploaded_files = st.file_uploader(
            f"📂 Upload up to {PLAN_DETAILS[st.session_state['user_plan']]['documents']} documents (Max 10 pages each)",
            type=["pdf", "docx", "xlsx", "csv"],
            accept_multiple_files=True
        )
        # ✅ Document Usage Selection (Moved Below Upload, Before Query Input)
        doc_usage_option = st.radio(
            "How should uploaded documents be used?",
            ["Support AI Response", "Summarize & Ask Direct Questions"],
            index=["Support AI Response", "Summarize & Ask Direct Questions"].index(
                st.session_state.get("doc_usage_option", "Support AI Response")
            ),
            key="doc_usage_tab1"  # ✅ Ensures unique ID to prevent Streamlit conflicts
        )
        st.session_state["doc_usage_option"] = doc_usage_option  # ✅ Ensure it persists

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
                    archetype=st.session_state["selected_archetype_tab1"],  # ✅ Correct variable
                    selected_experts=st.session_state["selected_experts_tab1"],  # ✅ Correct variable
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


                        if "full_report" not in st.session_state:
                            st.session_state["full_report"] = None  # ✅ Ensure `full_report` exists
                        if cached_response:
                            full_report = cached_response  # ✅ Use cached response if available
                        else:
                            full_report = generate_response(
                                query=query,
                                user_id=st.session_state["user_id"],
                                archetype=st.session_state["selected_archetype_tab1"],  # ✅ Correct variable
                                selected_experts=st.session_state["selected_experts_tab1"],
                                # ✅ Correct variable ✅ Ensure experts are passed correctly
                                uploaded_files=uploaded_files if uploaded_files else None,
                                # ✅ Ensure document uploads are handled
                                user_plan=st.session_state["user_plan"],
                                doc_usage_option=doc_usage_option
                            )
                            cache_response(cache_key, full_report)  # ✅ Cache AI response

                        if full_report:
                            st.session_state["full_report"] = full_report  # ✅ Store it persistently

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

            # ✅ Show Executive Summary Button ONLY if a report has been generated
            if "full_report" in st.session_state and st.session_state["full_report"]:
                if st.button("📝 Generate Executive Summary"):
                    with st.spinner("🔄 Summarizing AI Strategy Report..."):
                        summary_report = generate_summary(st.session_state["full_report"], st.session_state["user_id"])
                        st.session_state["summary_report"] = summary_report  # ✅ Store summary persistently

                # ✅ Always show the full AI-generated report
                if "full_report" in st.session_state and st.session_state["full_report"]:
                    st.subheader("📜 AI Strategy Report")
                    st.write(st.session_state["full_report"])

                # ✅ Show Executive Summary if available
                if "summary_report" in st.session_state and st.session_state["summary_report"]:
                    st.subheader("📄 Executive Summary (AI-Generated)")
                    st.write(st.session_state["summary_report"])



        # ✅ Strategy Report Generation Section (Independent Feature)
        # ✅ Tab 2: Structured Strategy Report (PDF)
        with tab2:
            st.subheader("📜 Stratogenic AI Execution Plan")

            st.markdown(
                "🚀 Generate a **structured AI-driven business strategy report** based on your industry, revenue model, and key business goals. "
                "This feature leverages **expert-backed insights, archetypal strategy approaches, and AI-driven execution plans**."
            )
            industry_option = st.selectbox(
                "📍 Select Industry (or choose 'Other' to enter manually)",
                ["Tech", "Retail", "Finance", "Healthcare", "Fundraising", "Charity", "Other"]
            )
            if industry_option == "Other":
                industry = st.text_input("📝 Enter Your Industry",
                                         placeholder="e.g., Climate Tech, Social Impact, Education")
            else:
                industry = industry_option
            goal = st.text_input("🎯 Business Goal", placeholder="Expand into a new market")
            revenue_model = st.selectbox("💰 Revenue Model", ["Subscription", "One-time purchase", "Freemium", "Other"])
            competitors = st.text_area("🏆 Competitor Names (Optional)")

            # ✅ Ensure Archetype is Stored in Session State to Prevent 'None' Issues
            if "selected_archetype_tab2" not in st.session_state:
                st.session_state["selected_archetype_tab2"] = list(archetype_prompts.keys())[
                    0]  # Default to first archetype

            st.session_state["selected_archetype_tab2"] = st.selectbox(
                "🎭 Select Your Archetype",
                options=list(archetype_prompts.keys()),
                index=list(archetype_prompts.keys()).index(st.session_state["selected_archetype_tab2"])
                # Preserve last selection
            )
            selected_archetype = st.session_state["selected_archetype_tab2"]

            # ✅ Ensure `selected_experts_tab2` is initialized before using it
            if "selected_experts_tab2" not in st.session_state:
                st.session_state["selected_experts_tab2"] = []  # ✅ Default to an empty list

            # ✅ Create expert selection widget WITHOUT overwriting session state after instantiation
            selected_experts_display_tab2 = st.multiselect(
                "🎓 Select Expert Insights",
                options=list(expert_prompts.keys()),
                default=st.session_state["selected_experts_tab2"],  # ✅ Preserve selection
                max_selections=3,
                key="selected_experts_tab2"  # ✅ Assign a unique key
            )

            # ✅ Instead of modifying session state, check the variable directly
            if "selected_experts_tab2" not in st.session_state:
                st.session_state["selected_experts_tab2"] = []  # ✅ Default to an empty list
            elif set(selected_experts_tab2_display) != set(st.session_state["selected_experts_tab2"]):
                st.session_state["selected_experts_tab2"] = selected_experts_tab2_display  # ✅ Update only when needed

                    # ✅ Ensure at least one expert is selected
            if not selected_experts_display_tab2:
                st.warning("⚠ Please select at least one expert.")

            if st.button("🚀 Generate Strategy Report"):
                if not selected_archetype:
                    st.warning("⚠ Please select an Archetype.")
                elif not selected_experts:
                    st.warning("⚠ Please select at least one Expert.")
                else:
                    structured_inputs = {
                        "industry": industry,
                        "goal": goal,
                        "revenue_model": revenue_model,
                        "competitors": competitors
                    }
                    if not st.session_state["selected_archetype_tab2"]:
                        st.warning("⚠ Please select an Archetype.")
                    elif not st.session_state["selected_experts_tab2"] or len(
                            st.session_state["selected_experts_tab2"]) == 0:
                        st.warning("⚠ Please select at least one Expert.")
                    else:
                        pdf_file = generate_strategy_pdf(
                            st.session_state["user_id"], structured_inputs, st.session_state["selected_archetype_tab2"],
                            st.session_state["selected_experts_tab2"]
                        )
                        st.success(f"✅ Strategy Report Generated! [Download Here]({pdf_file})")

    # ✅ Follow-Up Query Section (AFTER Report & Summary)
    if "initial_response" in st.session_state and st.session_state["initial_response"] and "full_report" in st.session_state:
        st.subheader("🔄 Follow-Up Query")
        follow_up_query = st.text_area("Enter your follow-up question:")


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
            ),
            key="doc_usage_tab2"  # ✅ Unique key to prevent duplicate ID error
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
                    archetype=st.session_state["selected_archetype_tab2"],  # ✅ Correct variable
                    selected_experts=st.session_state["selected_experts_tab2"],  # ✅ Correct variable
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

