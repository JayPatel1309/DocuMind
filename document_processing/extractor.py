from datetime import datetime
import mimetypes
from backend.database.dataentry import enter_data_documents,enter_data_documents_metadata,enter_data_documents_chunk,fetch_category_id
from vector_store.faiss_index import faiss_index
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import joblib
import re
import spacy
import PyPDF2 as pypdf2
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

model=joblib.load(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\Logistic_Model.joblib")
encoder=joblib.load(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\Logistic_Encoder.joblib")
embedder=SentenceTransformer(r"P:\AI-Powered Document Classification and Intelligent Indexing\ml\models\sentence_transformer_model")
def clean_text(text_sample):
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
    text_sample = re.sub('http\\S+\\s*', ' ', text_sample)
    text_sample = re.sub('RT|cc', ' ', text_sample)
    text_sample = re.sub('#\\S+', '', text_sample)
    text_sample = re.sub('@\\S+', '  ', text_sample)
    text_sample = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"""), ' ', text_sample)
    text_sample = re.sub(r'[^\x00-\x7f]', r' ', text_sample)
    text_sample = re.sub('\\s+', ' ', text_sample)
    text_sample=re.sub(r'\b(' + '|'.join(boilerplate_words) + r')\b\s*', "", text_sample, flags=re.IGNORECASE)
    return text_sample.lower()


def file_info(file_path_sample):
    file_name_sample = os.path.basename(file_path_sample)
    absolute_path_sample = os.path.abspath(file_path_sample)
    file_size_sample = os.path.getsize(file_path_sample)
    mime_type_sample, _ = mimetypes.guess_type(file_path_sample)
    return file_name_sample, absolute_path_sample, file_size_sample, mime_type_sample

def detail_extraction(text_sample):
    try:
        pattern = r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\s*,\s*\d{4}\b"
        matches = re.findall(pattern, text_sample, re.IGNORECASE)
        date_sample = matches[0]
    except:
        date_sample = None
    try :
        sentences_sample=text_sample.split("\n")
        title_sample=sentences_sample[0]
    except:
        title_sample = None
    try:
        author_search=re.search(r"From:\s*(.*)", text_sample)
        author=author_search.group(1)
        return date_sample, author,title_sample
    except:
        return date_sample, None, title_sample

def summary_creator(text_sample):
    sentences_sample = text_sample.split("\n")
    sentences_sample.pop()
    vectorizer = TfidfVectorizer(stop_words='english')
    text_vector = vectorizer.fit_transform([text_sample])
    words=vectorizer.get_feature_names_out()
    avg_scores = text_vector.mean(axis=0).tolist()[0]
    word_priorities = pd.DataFrame({'Word': words, 'Priority_Score': avg_scores})
    word_priorities = word_priorities.sort_values(by='Priority_Score', ascending=False)
    word_priorities_dict=(zip(word_priorities['Word'], word_priorities['Priority_Score']))
    score_words={}
    for words in word_priorities_dict:
        score=words[1]
        if 0.0 <= score <= 0.1:
            score_words[words[0]]=1
        elif 0.1 < score <= 0.2:
            score_words[words[0]]=2
        elif 0.2 < score <= 0.3:
            score_words[words[0]]=3
        else:
            score_words[words[0]]=4
    score_sentences={}
    for sentence in sentences_sample:
        score_sum=0
        for words in score_words.keys():
            if words in sentence:
                score_sum+=score_words[words]
            else :
                score_sum+=0
        score_sentences[sentence]=score_sum
    score_sentences = dict(sorted(score_sentences.items(), key=lambda item: item[1], reverse=True))
    score_sentences_list=list(score_sentences.keys())
    summary_text_sample= " ".join(score_sentences_list[:6])
    return summary_text_sample

def keytopics_find(text_sample):
    text_sample=clean_text(text_sample)
    doc_vector=embedder.encode([text_sample])
    cosine_sm_words={}
    words=text_sample.split(" ")
    words.pop()
    for word in words:
        word_vector=embedder.encode([word])
        similarity_status=cosine_similarity(doc_vector,word_vector)
        similarity_status=similarity_status[0][0].item()
        cosine_sm_words[word]=similarity_status
    cosine_sm_words=dict(sorted(cosine_sm_words.items(), key=lambda item: item[1], reverse=True))
    cosine_sm_words_list=list(cosine_sm_words.keys())
    return cosine_sm_words_list[:7]



#pdf reader
folder_path = Path(r"P:\AI-Powered Document Classification and Intelligent Indexing\data\doc_fin")
for path_object in folder_path.glob("*.pdf"):
    file_path = str(path_object)
    if os.path.exists(file_path):
        file_name, absolute_path, file_size, mime_type=file_info(file_path)
        print("File size is: ",file_size)
        print("File name is: ",file_name)
        print("File absolute path is : ",absolute_path)
        print("File type is : ",mime_type)
        reader=pypdf2.PdfReader(file_path)
        text = ''
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + ' '


        #print(text_sample)

        #splitting into sentences
        sentences=text.split("\n")
        sentences.pop()
        #labeling the texts
        nlp=spacy.load('en_core_web_sm')
        doc=nlp(text)

        date,author,title=detail_extraction(text)

        #Label extraction
        orgs=[]
        dates=[]
        for ent in doc.ents:
            if ent.label_=="ORG":
                orgs.append(ent.text)
            elif ent.label_=="DATE":
                dates.append(ent.text)
        text_sum=text
        text=clean_text(text)
        text_embedding=embedder.encode([text])
        predicted_class=model.predict(text_embedding)
        predicted_category=encoder.inverse_transform(predicted_class)[0]
        predict_id=fetch_category_id(predicted_category)
        print("Predicted Category:",predicted_category)
        safe_predicted_class = int(predicted_class[0])
        probabilities = model.predict_proba(text_embedding)[0]
        confidence = max(probabilities)
        safe_confidence = float(confidence)
        summary_text=summary_creator(text_sum)
        keytopics=keytopics_find(text)
        words=text.split(" ")
        chunk = []
        chunk_index=0

        enter_data_documents(str(file_name),absolute_path,mime_type,file_size,predict_id,safe_confidence,date)
        enter_data_documents_metadata(str(file_name),title,author,date,summary_text,keytopics)
        for word in words:
            if len(chunk)==200:
                chunk_string=" ".join(chunk)
                index=faiss_index(r'P:\AI-Powered Document Classification and Intelligent Indexing\vector_store\global_vector_index.faiss',chunk_string,embedder)
                enter_data_documents_chunk(file_name,chunk_index,chunk_string,index)
                chunk_index+=1
                chunk=[]
                print(index)
            chunk.append(word)

        if len(chunk)>0:
            chunk_string=" ".join(chunk)
            index = faiss_index(
                r'P:\AI-Powered Document Classification and Intelligent Indexing\vector_store\global_vector_index.faiss',
                chunk_string, embedder)
            enter_data_documents_chunk(file_name, chunk_index, chunk_string, index)
            chunk = []









