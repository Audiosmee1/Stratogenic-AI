# app/config.py

# app/config.py

PLAN_DETAILS = {
    "The Foundation (Free)": {
        "price": 0,
        "queries": 3,
        "documents": 1,
        "max_experts": 2,
        "model": "gpt-3.5-turbo",
        "follow_ups": 1,
        "summary_available": False,
        "report_depth": """
        🚀 **Generate a concise report that includes:**
        1️⃣ **Summary of key insights**
        2️⃣ **Three actionable steps**
        3️⃣ **One major risk to consider**
        4️⃣ **(Max Length: ~600-700 words)**
        """,
    },
    "The Tactician (£9/month)": {
        "price": 9,
        "queries": 8,
        "documents": 2,
        "max_experts": 3,
        "model": "gpt-4-turbo",
        "follow_ups": 2,
        "summary_available": False,
        "report_depth": """
        🚀 **Generate a detailed strategy report that includes:**
        1️⃣ **Structured execution steps (5-7 key actions)**
        2️⃣ **Risk assessment with mitigation strategies**
        3️⃣ **Strategic recommendations for the next 90 days**
        4️⃣ **(Max Length: ~2,500 words)**
        """,
    },
    "The Assembly (£19/month)": {
        "price": 19,
        "queries": 12,  # ✅ Adjusted to prevent confusion vs. Professional
        "documents": 3,
        "max_experts": 4,
        "model": "gpt-4-turbo",
        "follow_ups": 2,
        "summary_available": False,
        "report_depth": """
        🚀 **Generate an advanced business strategy report that includes:**
        1️⃣ **Detailed execution plan (7-10 key actions)**
        2️⃣ **Risk management insights and mitigation tactics**
        3️⃣ **Industry-specific recommendations**
        4️⃣ **Scaling strategies based on market trends**
        5️⃣ **(Max Length: ~4,000 words)**
        """,
    },
    "The Professional (£69/month)": {
        "price": 69,  # ✅ Increased price for better perceived value
        "queries": 15,  # ✅ Increased to ensure clear superiority over Assembly
        "documents": 5,
        "max_experts": 5,
        "model": "gpt-4-turbo",
        "follow_ups": 5,
        "follow_up_model": "gpt-3.5-turbo",  # ✅ Cost control measure for follow-ups
        "summary_available": True,
        "report_depth": """
        🚀 **Generate a professional-grade business strategy report that includes:**
        1️⃣ **Step-by-step execution plan for long-term success**
        2️⃣ **Comprehensive market risk analysis & mitigation**
        3️⃣ **Competitive landscape insights & growth hacking strategies**
        4️⃣ **Comparative investment models (£10K vs. £50K growth potential)**
        5️⃣ **(Max Length: ~5,500 words)**
        """,
    },
    "The Growth (£500/month)": {
        "price": 500,  # ✅ Reduced from £499 for simplicity
        "queries": 50,
        "documents": 10,  # ✅ Enforced 10-doc limit
        "max_experts": 5,
        "model": "gpt-4-turbo",
        "follow_ups": 10,  # ✅ Capped follow-ups at 10
        "follow_up_model": "gpt-4-turbo",  # ✅ Premium follow-ups
        "summary_available": True,
        "report_depth": """
        🚀 **Generate an enterprise-grade strategic report that includes:**
        1️⃣ **Full-scale growth roadmap (12-24 months)**
        2️⃣ **Market entry, scaling, and expansion insights**
        3️⃣ **AI-driven forecasting based on market patterns**
        4️⃣ **Comparative financial planning (ROI models for £50K, £100K, and £250K investments)**
        5️⃣ **(Max Length: ~8,000 words)**
        """,
    },
    "Enterprise (£5,000/month)": {
        "price": 5000,  # ✅ Kept same for high-end clients
        "queries": 100,
        "documents": 10,  # ✅ Capped at 10-doc max (10 pages each)
        "max_experts": 5,  # ✅ Enforced 5-expert limit
        "model": "gpt-4-turbo",
        "follow_ups": 10,  # ✅ Capped follow-ups at 10
        "follow_up_model": "gpt-4-turbo",  # ✅ Premium-level AI for top-tier users
        "summary_available": True,
        "report_depth": """
        🚀 **Generate a full enterprise-level market intelligence report that includes:**
        1️⃣ **Comprehensive strategic roadmap (24-36 months)**
        2️⃣ **Comparative analysis of multiple business strategies:**
            - 📊 *Investment of £10K vs. £100K vs. £1M: What changes?*
            - 📊 *High-risk, high-reward vs. conservative growth*
        3️⃣ **Global market trends, risk forecasting, and geopolitical considerations**
        4️⃣ **Executive team structuring, hiring roadmap, and leadership development**
        5️⃣ **(Max Length: ~10,000-12,500 words)**
        """,
    },
}