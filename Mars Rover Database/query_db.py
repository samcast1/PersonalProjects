import sqlite3
import pandas as pd

conn = sqlite3.connect("mars_photos.db")

query = """

    SELECT COUNT(rover) AS total
    FROM mars_photos
    GROUP BY rover

    """
df = pd.read_sql_query(query, conn)

pd.set_option('display.max_rows', None)  # Display all rows
pd.set_option('display.max_columns', None)  # Display all columns
pd.set_option('display.width', None)  # Adjust the display width
pd.set_option('display.max_colwidth', None)  # Adjust column width


print("Executing query: \n", query, "\n")
print("Query results: \n", df)

conn.close()
