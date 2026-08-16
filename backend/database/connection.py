import psycopg2 as pg
try:
    conn = pg.connect(
        dbname="DocuMind",
        user="postgres",
        password="12345",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    for category in categories:
        print(category)
except :
    print("Connection Error")