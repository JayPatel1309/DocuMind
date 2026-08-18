import PyPDF2 as pypdf2
import csv
import re
def clean_text(text):
    text = re.sub('http\\S+\\s*', ' ', text)
    text = re.sub('RT|cc', ' ', text)
    text = re.sub('#\\S+', '', text)
    text = re.sub('@\\S+', '  ', text)
    text = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"""), ' ', text)
    text = re.sub(r'[^\x00-\x7f]',r' ', text)
    text = re.sub('\\s+', ' ', text)
    return text.lower()
reader=pypdf2.PdfReader(r"P:\AI-Powered Document Classification and Intelligent Indexing\data\doc_tech\technical_dataset_batch_2-010.pdf")
first_page=reader.pages[0].extract_text()
first_page=clean_text(first_page)
category=first_page.split(" ")[0]
header=["Category","Content"]
content_text_list=first_page.split(" ")
content_text=" ".join(content_text_list[1:])
content=[category,content_text]
with open(f"P:\AI-Powered Document Classification and Intelligent Indexing\data\csv_dataset\extracted_text.csv", mode="a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(content)
