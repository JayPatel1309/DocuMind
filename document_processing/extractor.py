from datetime import datetime
import mimetypes
from backend.database.dataentry import enter_data_documents
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import joblib
import re
import spacy
import PyPDF2 as pypdf2
from sentence_transformers import SentenceTransformer


vectorizer = TfidfVectorizer()
def clean_text(text):
    boilerplate_words = [
        r"synergy", r"synergistic", r"synergize",
        r"drill[-]down", r"deep[-]dive",
        r"touch[-]base", r"circle[-]back",
        r"low[-]hanging fruit", r"moving forward",
        r"at the end of the day", r" paradigm shift",
        r"actionable insights", r"core competencies",
        r"value[-]add", r"think outside the box",
        r"wheelhouse", r"bandwidth"
    ]
    text = re.sub('http\\S+\\s*', ' ', text)
    text = re.sub('RT|cc', ' ', text)
    text = re.sub('#\\S+', '', text)
    text = re.sub('@\\S+', '  ', text)
    text = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"""), ' ', text)
    text = re.sub(r'[^\x00-\x7f]', r' ', text)
    text = re.sub('\\s+', ' ', text)
    text=re.sub( r'\b(' + '|'.join(boilerplate_words) + r')\b\s*', "", text, flags=re.IGNORECASE)
    return text.lower()
#pdf reader
file_path=r"P:\AI-Powered Document Classification and Intelligent Indexing\data\doc_leg\doc_leg_002.pdf"
if os.path.exists(file_path):
    file_name = os.path.basename(file_path)
    absolute_path = os.path.abspath(file_path)
    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    print("File size is: ",file_size)
    print("File name is: ",file_name)
    print("File absolute path is : ",absolute_path)
    print("File type is : ",mime_type)
    reader=pypdf2.PdfReader(file_path)
    text=reader.pages[0].extract_text()

    #print(text)

    #splitting into sentences
    sentences=text.split("\n")
    sentences.pop()
    #labeling the texts
    nlp=spacy.load('en_core_web_sm')
    doc=nlp(text)

    #date extraction
    pattern = r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\s*,\s*\d{4}\b"
    matches = re.findall(pattern, text, re.IGNORECASE)
    date=matches[0]
    print("Date :",date)
    postgres_timestamp = datetime.strptime(date, "%B %d, %Y")

    #author/from search
    try:
        author_search=re.search(r"From:\s*(.*)",text)
        author=author_search.group(1)
        print("Author/From: ",author)
    except:
        print("No author found")
    #Label extraction
    orgs=[]
    dates=[]
    for ent in doc.ents:
        if ent.label_=="ORG":
            orgs.append(ent.text)
        elif ent.label_=="DATE":
            dates.append(ent.text)

    #print("The orgs label \n",orgs)
    #print("The dates label \n",dates)
    #print("Previous sentences \n",sentences)
    #print("New sentences \n",sentences)
    text_organized=" ".join(sentences)
    text_organized=clean_text(text_organized)
    model=joblib.load(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\Logistic_Model.joblib")
    encoder=joblib.load(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\Logistic_Encoder.joblib")
    embedder=SentenceTransformer(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\sentence_transformer_model")
    text_embedding=embedder.encode([text_organized])
    predicted_class=model.predict(text_embedding)
    predicted_category=encoder.inverse_transform(predicted_class)[0]
    print("Predicted Category:",predicted_category)
    safe_predicted_class = int(predicted_class[0])
    probabilities = model.predict_proba(text_embedding)[0]
    confidence = max(probabilities)
    safe_confidence = float(confidence)
    enter_data_documents(file_name,file_path,mime_type,file_size,safe_predicted_class,safe_confidence,postgres_timestamp)











