import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import mysql.connector
from datetime import datetime

# Initialize the SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Database connection function
def connect_to_db():
    return mysql.connector.connect(
        host="wikiscrape-db.c3oiygc2awdx.us-east-2.rds.amazonaws.com",
        user="admin",
        password="wikiscrape",
        database="mydb"
    )

# Function to query the database
def get_data_from_db(date_range, event_type):
    db = connect_to_db()
    cursor = db.cursor(dictionary=True)
    
    # Query to select data based on date range and event type
    query = """
    SELECT * FROM wiki_events 
    WHERE STR_TO_DATE(date, '%M %d') BETWEEN STR_TO_DATE(%s, '%M %d') AND STR_TO_DATE(%s, '%M %d')
    AND year BETWEEN %s AND %s
    AND event_type = %s
    """
    cursor.execute(query, (date_range[0], date_range[1], date_range[2], date_range[3], event_type))
    data = cursor.fetchall()
    db.close()
    return pd.DataFrame(data)

# Function to calculate cosine similarity and find the most similar entry
def find_most_similar_entry(tag, data):
    tag_embedding = model.encode(tag)
    data['embedding'] = data['text'].apply(lambda x: model.encode(x))
    data['similarity'] = data['embedding'].apply(lambda x: util.pytorch_cos_sim(tag_embedding, x).item())
    return data.sort_values(by='similarity', ascending=False).iloc[0]

# Function to generate days for a selected month
def get_days_in_month(month):
    days_in_month = {
        'January': 31, 'February': 28, 'March': 31, 'April': 30, 'May': 31,
        'June': 30, 'July': 31, 'August': 31, 'September': 30, 'October': 31,
        'November': 30, 'December': 31
    }
    return list(range(1, days_in_month[month] + 1))

# Streamlit app
st.title("Welcome to WikiSimilar!")

# Date input
st.subheader("Select a date range")

# Month selection for start date
start_month = st.selectbox("Start Month", ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

# Generate days based on the selected month
start_days = get_days_in_month(start_month)
start_day = st.selectbox("Start Day", start_days)

# Month selection for end date
end_month = st.selectbox("End Month", ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

# Generate days based on the selected month
end_days = get_days_in_month(end_month)
end_day = st.selectbox("End Day", end_days)

# Year range input
st.subheader("Select a year range")
start_year, end_year = st.slider(
    "Year Range",
    min_value=-300,
    max_value=datetime.now().year,
    value=(1500, 1800)
)

# Event type input
st.subheader("Select event type")
event_type = st.selectbox("Event Type", ["event", "birth", "death"])

# Tag input
st.subheader("Is there anything in particular you'd like to search for?")
tag = st.text_input("Enter a tag")

# Search button
if st.button("Search"):
    if start_month and end_month and start_day and end_day and tag:
        # Create date strings in 'Month Day' format
        start_date = f"{start_month} {start_day}"
        end_date = f"{end_month} {end_day}"
        date_range = (start_date, end_date, start_year, end_year)
        
        with st.spinner("Searching..."):
            data = get_data_from_db(date_range, event_type)
            
            if not data.empty:

                result = find_most_similar_entry(tag, data)
                st.subheader("Result")
                st.write(f"**Date:** {result['date']}")
                st.write(f"**Year:** {result['year']}")
                st.write(f"**Event:** {result['text']}")
                
                st.subheader("Learn more below!")
                for i in range(1, 21):
                    tag_col = f"tag_{i}"
                    link_col = f"link_{i}"
                    if pd.notna(result[tag_col]) and pd.notna(result[link_col]):
                        st.write(f"**{result[tag_col]}:** {result[link_col]}")
            else:
                st.write("No results found for the selected date range and event type.")