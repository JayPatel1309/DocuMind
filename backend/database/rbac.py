import psycopg2


def get_connection():
    return psycopg2.connect(
        dbname="DocuMind",
        user="postgres",
        password="12345",
        host="localhost",
        port="5432"
    )


def is_authorized_to_view(username, document_category):
    role = None
    if username:
        try:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT role FROM users WHERE username = %s;", (username,))
                result = cur.fetchone()
                if result and result[0]:
                    role = result[0].upper()
            finally:
                conn.close()
        except Exception:
            role = None

    if role == 'ADMIN':
        return True

    category = (document_category or "").strip().lower()
    if category in ['legal', 'contracts']:
        return False

    return True


def authenticate_user(username, password):
    if not username:
        return None
    try:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, username, role FROM users WHERE username = %s AND password_hash = %s;",
                (username, password)
            )
            row = cur.fetchone()
            if row:
                return {"user_id": row[0], "username": row[1], "role": row[2]}
            return None
        finally:
            conn.close()
    except Exception:
        return None
