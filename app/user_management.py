import bcrypt
from app.database import get_db_connection, release_db_connection
from app.config import PLAN_DETAILS

# ✅ Hash password before storing
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# ✅ Verify password during login
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# ✅ Register new user
def register_user(email, password):
    """Registers a new user with hashed password."""
    conn = get_db_connection()
    if not conn:
        return "❌ Database connection failed."

    cursor = None  # ✅ Ensure cursor is initialized
    try:
        hashed_pw = hash_password(password)
        cursor = conn.cursor()

        # ✅ Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s;", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return "❌ Email already registered. Try logging in."

        # ✅ Insert new user
        cursor.execute("INSERT INTO users (email, password_hash, plan) VALUES (%s, %s, %s) RETURNING id;",
                       (email, hashed_pw, "The Foundation (Free)"))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)

# ✅ Authenticate user
def authenticate_user(email, password):
    """Authenticates user with email & password, and ensures their plan name is updated if needed."""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = None  # ✅ Ensure cursor is initialized

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, plan, is_admin FROM users WHERE email = %s;", (email,))
        user = cursor.fetchone()

        if user and check_password(password, user[2]):
            user_plan = user[3]

            # ✅ If the user's plan name is outdated, update it
            if user_plan not in PLAN_DETAILS:
                corrected_plan = "The Professional (£69/month)" if "Professional" in user_plan else "The Foundation (Free)"
                print(f"🔄 Auto-updating plan for {email} from {user_plan} to {corrected_plan}")

                cursor.execute("UPDATE users SET plan = %s WHERE id = %s;", (corrected_plan, user[0]))
                conn.commit()
                user_plan = corrected_plan  # ✅ Ensure the updated plan is used

            return {
                "user_id": user[0],
                "email": user[1],
                "plan": user_plan,  # ✅ Ensures the updated plan is returned
                "is_admin": bool(user[4])
            }
        return None
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)


# ✅ Update user plan
def update_user_plan(user_identifier, new_plan):
    """Updates a user's plan using either user_id or email."""
    conn = get_db_connection()
    if not conn:
        return "❌ Database connection failed."

    cursor = None  # ✅ Initialize cursor

    try:
        cursor = conn.cursor()
        if isinstance(user_identifier, int):  # User ID
            cursor.execute("UPDATE users SET plan = %s WHERE id = %s;", (new_plan, user_identifier))
        else:  # Email
            cursor.execute("UPDATE users SET plan = %s WHERE email = %s;", (new_plan, user_identifier))

        conn.commit()
        return f"✅ Plan updated to {new_plan} successfully."
    except Exception as e:
        print(f"❌ Failed to update user plan: {e}")
        return "❌ Error updating plan."
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)

def check_one_time_access(user_id):
    """Checks if the user has remaining one-time access for Enterprise Report."""
    conn = get_db_connection()
    if not conn:
        return False

    cursor = None  # ✅ Ensure cursor is initialized

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT used, follow_ups_remaining FROM enterprise_access WHERE user_id = %s;", (user_id,))
        result = cursor.fetchone()
        return bool(result and not result[0] and result[1] > 0)
    except Exception as e:
        print(f"❌ One-time access check failed: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)