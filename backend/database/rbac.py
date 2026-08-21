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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username = %s;", (username,))
    result = cur.fetchone()
    conn.close()
    
    if not result:
        return False # User not found
    
    role = result[0].upper()
    
    if role == 'ADMIN':
        return True
        
    if role == 'VIEWER':
        if document_category.lower() in ['finance', 'legal']:
            return False
        return True
        
    return False

# You can import is_authorized_to_view in your search.py API route!
