from app.database import get_db_connection, release_db_connection  # ✅ Use connection pooling

def grant_one_time_access(user_id):
    """Grants access to a one-time enterprise report with 2 follow-ups."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO enterprise_access (user_id, used, follow_ups_remaining)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET used = FALSE, follow_ups_remaining = 2;
        """, (user_id, False, 2))
        conn.commit()
        cursor.close()
        release_db_connection(conn)
    return True

def check_one_time_access(user_id):
    """Checks if the user has remaining one-time access."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT used, follow_ups_remaining FROM enterprise_access WHERE user_id = %s;", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    release_db_connection(conn)
    if result and not result[0] and result[1] > 0:
        return result[1]  # ✅ Return remaining follow-ups
    return 0

def use_one_time_follow_up(user_id):
    """Reduces the number of follow-ups for one-time users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE enterprise_access SET follow_ups_remaining = follow_ups_remaining - 1 WHERE user_id = %s;", (user_id,))
    conn.commit()
    cursor.close()
    release_db_connection(conn)
