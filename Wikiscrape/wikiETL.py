# FINAL ETL SCRIPT !!!!

import pandas as pd
from urllib.parse import unquote
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from functools import reduce
from itertools import islice
import os
from urllib.parse import urlparse
import re
import string
import datetime
import mysql.connector

def wikiscrape(date):

  url = f"https://www.wikipedia.org/wiki/{date}"

  body_class = "mw-content-ltr"

  opts = FirefoxOptions()
  opts.add_argument("--headless")

  print("Initializing web driver . . . ")
  driver = webdriver.Firefox(options=opts)
  print('Webdriver initialized! \n')
  print('Acecssing url . . .')
  driver.get(url)
  print("Url acessed! \n")
  time.sleep(5)


  def get_entries(driver, body_class):
      body = driver.find_element(By.CLASS_NAME, body_class)
      entry_groups = body.find_elements(By.TAG_NAME, "ul")

      # Limit to the first nine <ul> tags
      entry_groups = entry_groups[:9]

      # Define the slicing ranges for each category
      event_end = 3
      birth_end = 6

      # Extract and categorize the entries
      def extract_entries(slice_start, slice_end):
          return reduce(
              lambda acc, ul: acc + ul.find_elements(By.TAG_NAME, "li"),
              islice(entry_groups, slice_start, slice_end),
              []
          )

      # Extract entries for events, births, and deaths
      event_entries = extract_entries(0, event_end)
      birth_entries = extract_entries(event_end, birth_end)
      death_entries = extract_entries(birth_end, None)

      # Debug: Print out the number of entries for each category
      print(f"Events: {len(event_entries)} items")
      print(f"Births: {len(birth_entries)} items")
      print(f"Deaths: {len(death_entries)} items")

      return event_entries, birth_entries, death_entries

# Example usage
  event_entries, birth_entries, death_entries = get_entries(driver, body_class)

  def collect_info(entry):

    raw_text = entry.text

    text = re.sub(r'\[\d+\]', '', raw_text).strip()

    details = entry.find_elements(By.TAG_NAME, "a")
    links = []
    for detail in details:
        if not detail.text.isdigit():
            url = detail.get_attribute("href")
            parsed_url = urlparse(url)
            last_part_of_url = os.path.split(parsed_url.path)[-1]
            tag = last_part_of_url.replace("_", " ")
            links.append((tag, url))

    return text, links

  event_data = [collect_info(entry) for entry in event_entries]
  birth_data = [collect_info(entry) for entry in birth_entries]
  death_data = [collect_info(entry) for entry in death_entries]


  driver.quit()

  return date, event_data, birth_data, death_data

def wikiload():

    # Establish a connection to the MySQL database
    connection = mysql.connector.connect(
    host="wikiscrape-db.c3oiygc2awdx.us-east-2.rds.amazonaws.com",
    user="admin",
    password="wikiscrape",
    database="mydb"   #
    )

    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wiki_events_12 (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date VARCHAR(20),
        year VARCHAR(10),
        event_type VARCHAR(10),
        text TEXT,
        tag_1 VARCHAR(100), link_1 TEXT,
        tag_2 VARCHAR(100), link_2 TEXT,
        tag_3 VARCHAR(100), link_3 TEXT,
        tag_4 VARCHAR(100), link_4 TEXT,
        tag_5 VARCHAR(100), link_5 TEXT,
        tag_6 VARCHAR(100), link_6 TEXT,
        tag_7 VARCHAR(100), link_7 TEXT,
        tag_8 VARCHAR(100), link_8 TEXT,
        tag_9 VARCHAR(100), link_9 TEXT,
        tag_10 VARCHAR(100), link_10 TEXT,
        tag_11 VARCHAR(100), link_11 TEXT,
        tag_12 VARCHAR(100), link_12 TEXT,
        tag_13 VARCHAR(100), link_13 TEXT,
        tag_14 VARCHAR(100), link_14 TEXT,
        tag_15 VARCHAR(100), link_15 TEXT,
        tag_16 VARCHAR(100), link_16 TEXT,
        tag_17 VARCHAR(100), link_17 TEXT,
        tag_18 VARCHAR(100), link_18 TEXT,
        tag_19 VARCHAR(100), link_19 TEXT,
        tag_20 VARCHAR(100), link_20 TEXT,
        -- add more tags/links if necessary
        INDEX (date)
    )
    ''')


    dates = []
    for month in ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']:
        for day in range(1,32):
            try:
                date_str = f'{month} {day}'
                valid = bool(datetime.datetime.strptime(date_str, '%B %d'))
                if valid:
                    dates.append(date_str)
            except ValueError:
                continue

    def wikicollate(query_date):

        query_date = query_date.replace(" ", "_")
        date, event_data, birth_data, death_data = wikiscrape(query_date)
        date = date.replace("_", " ")

        def prepare_data(date, event_type, data_list):

            columns = ['date', 'year', 'event_type', 'text'] + \
            [f'tag_{i+1}' for i in range(20)] + [f'link_{i+1}' for i in range(20)]

            placeholder = ', '.join(['%s' for _ in range(len(columns))])

            tags = [None] * 20
            link_urls = [None] * 20

            for text, links in data_list:
                year = text.split(" ")[0]
                if year == 'AD':
                  print("Converting year from 'AD' . . .")
                  year = text.split(" ")[1]
                  print("Converted year:", year)

                if not year.isdigit():
                  print("Whole text: ", text)
                  print('Non digit Year:', year)
                  match = re.search(r'\d+', text)
                  if match:
                    year = match.group()
                    print("Extracted Year:", year)
                  else:
                    print("No digits found in text")
                    continue

                text = " ".join(text.split(" ")[2:])

                if text.startswith("–"):
                  print('Text starts with dash:', text)
                  text = text[1:].strip()  # Remove the dash and any leading whitespace
                  print('Text after dash:', text)
                  try:
                    print('Trying to convert year: ', year)
                    year = int(year) * -1  # Multiply the year by -1
                    print('Converted year: ', year) 
                  except Exception as e:
                     print("Unable to convert year properly: ", e)
                     
                     
                row = [date, year, event_type, text]

                for i, (tag, link) in enumerate(links[:20]):  # Limit to the first 20 tags/links
                    tag = unquote(tag).strip()
                    if not tag == date:
                        tags[i] = tag
                        link_urls[i] = link

              # Extend the row with tags and links
                row.extend(tags)
                row.extend(link_urls)

              # Ensure the row has the correct number of columns
                while len(row) < len(columns):
                    row.append(None)

              # Insert the row into the MySQL database
                cursor.execute(f'''
                    INSERT INTO wiki_events_12 ({', '.join(columns)})
                    VALUES ({placeholder})
                ''', row)

        prepare_data(date, 'event', event_data)
        prepare_data(date, 'birth', birth_data)
        prepare_data(date, 'death', death_data)

        connection.commit()

    for query_date in dates:
      print(f"Processing date: {query_date} . . .")
      wikicollate(query_date)
      print(f"Successfully collected {query_date}. \n")

    cursor.close()
    connection.close()

wikiload()