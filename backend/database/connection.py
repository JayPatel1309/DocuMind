import os

import psycopg2 as pg
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "DocuMind")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (role IN ('ADMIN', 'HR', 'FINANCE', 'LEGAL', 'TECHNICAL', 'USER'))
);

CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    document_id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(20),
    file_size BIGINT,
    category_id INTEGER
        REFERENCES categories(category_id),
    classification_confidence DECIMAL(5,4),
    uploaded_by INTEGER
        REFERENCES users(user_id),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'PENDING',
    CHECK (
        processing_status IN (
            'PENDING',
            'PROCESSING',
            'COMPLETED',
            'FAILED'
        )
    )
);

CREATE TABLE IF NOT EXISTS document_metadata (
    metadata_id SERIAL PRIMARY KEY,
    document_id INTEGER UNIQUE NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,
    title TEXT,
    author TEXT,
    document_date DATE,
    summary TEXT,
    key_topics TEXT[]
);

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    chunk_text TEXT NOT NULL,
    embedding_id INTEGER,
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS access_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER
        REFERENCES users(user_id),
    document_id INTEGER
        REFERENCES documents(document_id),
    action VARCHAR(30) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ON CONFLICT DO NOTHING makes this safe to re-run without duplicating rows.
SEED_CATEGORIES_SQL = """
INSERT INTO categories (category_name, description)
VALUES
    ('Finance', 'Financial documents and reports'),
    ('HR', 'Human resource documents'),
    ('Legal', 'Legal documents'),
    ('Contracts', 'Contracts and agreements'),
    ('Technical', 'Technical reports'),
    ('Other', 'Other documents')
ON CONFLICT (category_name) DO NOTHING;
"""


def main() -> None:
    conn = None
    try:
        conn = pg.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        cur = conn.cursor()

        cur.execute(SCHEMA_SQL)
        cur.execute(SEED_CATEGORIES_SQL)
        conn.commit()

        cur.execute("SELECT category_id, category_name FROM categories ORDER BY category_id")
        print("Categories in DB:")
        for category in cur.fetchall():
            print(" ", category)

    except Exception as e:
        print("Connection/Schema Error:", e)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
