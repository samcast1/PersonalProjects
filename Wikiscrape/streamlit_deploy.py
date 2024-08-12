import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import mysql.connector

# Initialize the SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect to the database
def connect_to_db():
    return mysql.connector.connect(
        host="wikiscrape-db.c3oiygc2awdx.us-east-2.rds.amazonaws.com",
        user="admin",
        password="wikiscrape",
        database="mydb"  
    )

def get_data_from_db(date_range, event_type):
    db = connect_to_db()
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM wiki_events_12 WHERE date BETWEEN %s AND %s AND event_type = %s"
    cursor.execute(query, (date_range[0], date_range[1], event_type))
    data = cursor.fetchall()
    db.close()
    return pd.DataFrame(data)

def find_most_similar_entry(tag, data):
    tag_embedding = model.encode(tag)
    data['embedding'] = data['text'].apply(lambda x: model.encode(x))
    data['similarity'] = data['embedding'].apply(lambda x: util.pytorch_cos_sim(tag_embedding, x).item())
    return data.sort_values(by='similarity', ascending=False)

# Streamlit UI
st.title("Wikipedia Data Query")

date_range = st.date_input("Date Range", [])
event_type = st.selectbox("Event Type", ["Events", "Births", "Deaths"])
tag = st.text_input("Tag")

if st.button("Search"):
    if date_range and tag:
        data = get_data_from_db(date_range, event_type)
        results = find_most_similar_entry(tag, data)
        st.write("Top results:")
        st.write(results[['date', 'year', 'text', 'links']].head(5))

