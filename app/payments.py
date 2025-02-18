import stripe
import os
from app.database import get_db_connection, release_db_connection  # ✅ Use connection pooling
from app.config import PLAN_DETAILS  # ✅ Import PLAN_DETAILS
from app.user_management import update_user_plan  # ✅ Ensure function is imported

# ✅ Load Stripe API Key from Environment Variables
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def process_upgrade(user_id, new_plan):
    """Handles user plan upgrades via Stripe."""
    if new_plan not in PLAN_DETAILS:
        return "Invalid Plan"
    try:
        update_user_plan(user_id, new_plan)
        return f"Plan updated to {new_plan} successfully."
    except Exception as e:
        print(f"❌ Plan upgrade failed: {e}")
        return "An error occurred. Please try again later."

def process_one_time_payment(user_id, amount=25):
    """Handles a one-time Stripe payment for an enterprise-level report with 2 follow-ups."""
    try:
        # ✅ Create a Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": "One-Time Enterprise Strategy Report",
                        "description": "Full AI-generated strategy with 2 follow-up queries.",
                    },
                    "unit_amount": int(amount * 100),  # Convert to pence
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=os.getenv("SUCCESS_URL", "http://localhost:8501/success"),
            cancel_url=os.getenv("CANCEL_URL", "http://localhost:8501/cancel"),
        )

        # ✅ Store purchase in database
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed")
            return None

        cursor = None  # ✅ Initialize cursor to prevent reference errors

        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO enterprise_access (user_id, used, follow_ups_remaining)
                VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET used = FALSE, follow_ups_remaining = 2;
            """, (user_id, False, 2))
            conn.commit()
        except Exception as e:
            print(f"❌ Database error: {e}")
        finally:
            if cursor:  # ✅ Only close cursor if it was successfully assigned
                cursor.close()
            release_db_connection(conn)

        return session.url
    except Exception as e:
        print(f"❌ Payment Processing Failed: {e}")
        return None


