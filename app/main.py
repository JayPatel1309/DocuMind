from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from backend.database.connection  import Base, engine, get_db
from sqlalchemy import text
Base.metadata.create_all(bind=engine)
app = FastAPI()
"""
@app.get("/")
def check_connection(db: Session = Depends(get_db)):
  return {"message": "Database session successfully established!"}
"""


@app.get("/")
def get_users_raw(db: Session = Depends(get_db)):
  rows = db.execute(text("SELECT * FROM categories")).mappings().all()
  return [dict(row) for row in rows]