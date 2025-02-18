from psycopg2 import pool
import os
from dotenv import load_dotenv
from typing import Optional

# ✅ Load environment variables
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# ✅ Initialize connection pool
db_pool: Optional[pool.SimpleConnectionPool] = None

def init_db_pool():
    """Initializes the database connection pool and creates tables on startup."""
    global db_pool
    if db_pool is not None:
        return  # ✅ Prevent reinitialization if already initialized

    try:
        db_pool = pool.SimpleConnectionPool(1, 10,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        if db_pool:
            print("✅ Connection pool initialized successfully!")
            create_users_table()
            create_query_logs_table()
            create_user_feedback_table()
        else:
            print("❌ Connection pool creation failed: Pool is None.")

    except Exception as e:
        db_pool = None  # ✅ Ensure db_pool is reset if failure occurs
        print(f"❌ Connection pool initialization failed: {e}")

def get_db_connection():
    """Retrieves a database connection from the pool safely."""
    global db_pool
    if db_pool is None:
        print("⚠️ Database connection pool is not initialized. Attempting to reinitialize...")
        init_db_pool()

    if db_pool:
        try:
            conn = db_pool.getconn()
            if conn:
                conn.autocommit = True
                return conn  # ✅ Returns only `conn`, not a tuple
        except Exception as e:
            print(f"❌ Failed to get DB connection: {e}")

    return None  # ✅ Returns only `None`

def release_db_connection(conn):
    """Safely releases the database connection back to the pool."""
    global db_pool
    if conn:
        try:
            if db_pool:
                db_pool.putconn(conn, close=False)  # ✅ Only release if `conn` exists
            else:
                print("⚠️ Connection pool not available. Closing connection manually.")
                conn.close()  # ✅ Closes manually if the pool is uninitialized
        except Exception as e:
            print(f"❌ Failed to release DB connection: {e}")

# ✅ Create Users Table
def create_users_table():
    """Creates the users table if it does not exist."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                plan TEXT DEFAULT 'The Foundation (Free)',
                is_admin BOOLEAN DEFAULT FALSE,  
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("✅ Users table ready.")
    except Exception as e:
        print(f"❌ Failed to create users table: {e}")
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)

# ✅ Create Query Logs Table
def create_query_logs_table():
    """Creates the query logs table if it does not exist."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                query TEXT NOT NULL,
                plan TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("✅ Query logs table ready.")
    except Exception as e:
        print(f"❌ Failed to create query logs table: {e}")
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)

# ✅ Create User Feedback Table
def create_user_feedback_table():
    """Creates the user feedback table if it does not exist."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                query TEXT NOT NULL,
                feedback_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("✅ User Feedback table ready.")
    except Exception as e:
        print(f"❌ Failed to create user feedback table: {e}")
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)

# ✅ Store user query
def log_user_query(user_id, query, response, plan):
    """Stores user query logs along with AI responses."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO query_logs (user_id, query, response, plan)
            VALUES (%s, %s, %s, %s);
        """, (user_id, query, response, plan))
        conn.commit()
    except Exception as e:
        print(f"❌ Failed to log user query: {e}")
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)


def get_recent_queries_with_responses(user_id, limit=10):
    """Fetches the most recent queries along with their responses."""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = None
    try:
        cursor = conn.cursor()

        # ✅ Check if 'response' column exists before querying
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'query_logs' AND column_name = 'response';
        """)
        column_exists = cursor.fetchone()

        if not column_exists:
            print("⚠️ Column 'response' does not exist in query_logs. Returning only queries.")
            cursor.execute("""
                SELECT query, created_at 
                FROM query_logs 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s;
            """, (user_id, limit))
            queries = [(q[0], "No response stored", q[1]) for q in cursor.fetchall()]
        else:
            cursor.execute("""
                SELECT query, response, created_at 
                FROM query_logs 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s;
            """, (user_id, limit))
            queries = cursor.fetchall()

        return queries  # ✅ Returns list of (query, response, timestamp)
    except Exception as e:
        print(f"❌ Failed to fetch recent queries: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)


# ✅ Store user feedback
def log_user_feedback(user_id, query, feedback_text):
    """Stores user feedback in the database."""
    conn = get_db_connection()
    if not conn:
        return

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_feedback (user_id, query, feedback_text, created_at)
            VALUES (%s, %s, %s, NOW());
        """, (user_id, query, feedback_text))
        conn.commit()
    except Exception as e:
        print(f"❌ Failed to log user feedback: {e}")
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)

# ✅ Fetch user details by email
def get_user_by_email(email):
    """Fetches user details by email."""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, plan, is_admin FROM users WHERE email = %s;", (email,))
        user = cursor.fetchone()
        return user
    except Exception as e:
        print(f"❌ Failed to fetch user by email: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        release_db_connection(conn)
