# FINAL SCRIPT

import requests
import pandas as pd
import json
import sqlite3

API_KEY = "caiRqv6GXE0cYaLU2cPqpJy9sAQDfw711n1UEaTF"

BASE_URL = 'https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos'

def fetch_mars_photos(sol, camera=None):
    params = {
        'sol': sol,
        'api_key': API_KEY
    }
    if camera:
        params['camera'] = camera
    response = requests.get(BASE_URL, params=params)
    return response.json()

def get_max_sol():
  photos_data = fetch_mars_photos(sol=0)
  photos = photos_data['photos']
  max_sol = [photo['rover']['max_sol'] for photo in photos]
  max_sol = sorted(set(max_sol))
  return max_sol[0]

print()

print("Obtaining max sol . . .")
max_sol = get_max_sol()
print("Max sol: ", max_sol, "\n")


for i in range(180):
  print(f"Fetching photos for day {i+1}/180 . . .")
  photos_data = fetch_mars_photos(sol=(max_sol - i))


  # Extracting relevant information from the data
  photos = photos_data['photos']
  photos_df = pd.DataFrame([{
      'id': photo['id'],
      'sol': photo['sol'],
      'camera': photo['camera']['name'],
      'img_src': photo['img_src'],
      'earth_date': photo['earth_date'],
      'rover': photo['rover']['name'],
      'status': photo['rover']['status'],
      'max_sol': photo['rover']['max_sol'],
      'total_photos': photo['rover']['total_photos'],
      'launch_date': photo['rover']['launch_date'],
      'landing_date': photo['rover']['landing_date']
  } for photo in photos])

  if len(photos_df) == 0 :
    print(f"No photos recorded for day {i +1} . . . \n")
  else :
    print("Photos collected! \n")

    # Connect to SQLite database

    print("Loading photos to database. . .")
    conn = sqlite3.connect('mars_photos.db')
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mars_photos (
        id INTEGER PRIMARY KEY,
        sol INTEGER,
        camera TEXT,
        img_src TEXT,
        earth_date TEXT,
        rover TEXT,
        status TEXT,
        max_sol INTEGER,
        total_photos INTEGER,
        launch_date TEXT,
        landing_date TEXT
    )
    ''')
    conn.commit()

    def insert_data_into_db(photos_df):
        for _, row in photos_df.iterrows():
            cursor.execute('''
            INSERT INTO mars_photos (id, sol, camera, img_src, earth_date, rover, status, max_sol, total_photos, launch_date, landing_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            ''', (row['id'], row['sol'], row['camera'], row['img_src'], row['earth_date'], row['rover'],
                    row['status'], row['max_sol'], row['total_photos'], row['launch_date'], row['landing_date']))

        conn.commit()  # Save changes
        conn.close()

    # Example: Inserting latest data
    insert_data_into_db(photos_df)

    print(f"Success. Day {i+1}/180 photos are in database.")
