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
    conn.close()
