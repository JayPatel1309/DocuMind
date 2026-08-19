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
def extract_metadata(file_path):
    if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
    file_name = os.path.basename(file_path)
    absolute_path = os.path.abspath(file_path)
    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    stat_info = os.stat(file_path)
    created_time = datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc)
    cur = conn.cursor()
    insert_query = "INSERT INTO documents (filename,file_path,file_type,file_size,category_id,classification_confidence,uploaded_by,upload_date,processing_status) VALUES (%s, %s, %s,%s, %s, %s,%s, %s,%s);"
    record_to_insert = (file_name,absolute_path, mime_type, int(file_size),4,1,1,created_time,"COMPLETED")
    cur.execute(insert_query, record_to_insert)

#for i in range(0,10):
    file_path=(r"P:\AI-Powered Document Classification and Intelligent Indexing\data\doc_contrats\contracts_dataset_final-050"+".pdf")
    extract_metadata(file_path)
conn.commit()
conn.close()
