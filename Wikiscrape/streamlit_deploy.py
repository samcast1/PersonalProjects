import streamlit as st
import pandas as pd
from transformers import SentenceTransformer, util
import mysql.connector

# Initialize the SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect to the database
def connect_to_db():
    return mysql.connector.connect(
        host="your_db_host",
        user="your_db_user",
        password="your_db_password",
        database="your_db_name"
    )

def get_data_from_db(date_range, event_type):
    db = connect_to_db()
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM your_table WHERE date BETWEEN %s AND %s AND event_type = %s"
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
event_type = st.selectbox("Event Type", ["Type1", "Type2", "Type3"])
tag = st.text_input("Tag")

if st.button("Search"):
    if date_range and tag:
        data = get_data_from_db(date_range, event_type)
        results = find_most_similar_entry(tag, data)
        st.write("Top results:")
        st.write(results[['date', 'year', 'text', 'links']].head(5))

