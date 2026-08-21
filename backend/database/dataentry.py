from fileinput import filename

import psycopg2
import os
from datetime import datetime, timezone
import mimetypes


conn = psycopg2.connect(
    dbname="DocuMind",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
def enter_data_documents(file_name,absolute_path,mime_type,file_size,category_id,classification_confidence,created_time):
    cur = conn.cursor()
    insert_query = "INSERT INTO documents (filename,file_path,file_type,file_size,category_id,classification_confidence,uploaded_by,upload_date,processing_status) VALUES (%s, %s, %s,%s, %s, %s,%s, %s,%s);"
    record_to_insert = (file_name,absolute_path, mime_type, int(file_size),category_id,classification_confidence,1,created_time,"COMPLETED")
    cur.execute(insert_query, record_to_insert)
    conn.commit()
def enter_data_documents_metadata(doc_name,title,author,document_date,summary,keytopics):
    cur = conn.cursor()
    insert_query="INSERT INTO document_metadata (document_id,title,author,document_date,summary,key_topics) VALUES (%s,%s,%s,%s,%s,%s);"
    document_id = fetch_document_id(doc_name)
    record_to_insert = (document_id,title,author,document_date,summary,keytopics)
    cur.execute(insert_query, record_to_insert)
    conn.commit()

def enter_data_documents_chunk(doc_name,chunk_index,chunk_text,embedding_id):
    cur = conn.cursor()
    insert_query = "INSERT INTO document_chunks (document_id,chunk_index,page_number,chunk_text,embedding_id) VALUES (%s,%s,%s,%s,%s);"
    page_number=1
    document_id = fetch_document_id(doc_name)
    record_to_insert = (document_id,chunk_index,page_number,chunk_text,embedding_id)
    cur.execute(insert_query, record_to_insert)
    conn.commit()

def fetch_document_chunk(index):
    cur = conn.cursor()
    cur.execute("SELECT chunk_text FROM document_chunks WHERE embedding_id = %s;", (index,))
    chunk_list = cur.fetchone()
    return chunk_list[0] if chunk_list else None

def fetch_document_id(doc_name):
    cur = conn.cursor()
    cur.execute("SELECT document_id FROM documents WHERE filename = %s;", (doc_name,))
    document_id = cur.fetchone()
    return document_id[0] if document_id else None
def fetch_category_id(category_name):
    cur = conn.cursor()
    cur.execute("SELECT category_id FROM categories WHERE category_name = %s;", (category_name,))
    id=cur.fetchone()
    return id[0] if id else None
