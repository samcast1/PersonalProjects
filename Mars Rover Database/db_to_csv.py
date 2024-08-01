import sqlite3
import pandas as pd

conn = sqlite3.connect("mars_photos.db")

query = """

    SELECT * 
    FROM mars_photos

    """
df = pd.read_sql_query(query, conn)

print("Sample of database to save: \n", df.head(), "\n")
print("Saving results as csv . . .")

filepath = r"""C:\Users\casti\OneDrive\Documents\PersonalProjects\Mars Rover Database\photo_data\photo_data.csv"""
df.to_csv(filepath, index=False)

print("Results saved!")

conn.close()
