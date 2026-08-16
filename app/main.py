from fastapi import FastAPI
from backend.database.connection import connection
app = FastAPI()


@app.get("/")
async def root():
    with connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM categories")
            categories = cur.fetchall()
