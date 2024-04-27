#!/usr/bin/env python
# coding: utf-8

# In[1]:


import findspark
findspark.init()
import pyspark
from pyspark.sql import SparkSession
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_palette('deep')


# In[2]:


spark = SparkSession.builder \
        .appName('Online-Retail-Visualization') \
        .getOrCreate()


# In[3]:


df = spark.read.csv(r's3://sc-projectbucket/PySpark SparkSQL E-Commerce Analysis/On_Re.csv', header=True, inferSchema=True)


# In[4]:


df.printSchema()


# In[5]:


df.show(10)


# In[6]:


filtered = df.filter(df.Quantity > 2000).orderBy(df.Quantity, ascending=False)
sel = filtered.select('Description','Quantity')
dfp = sel.toPandas()
dfp10 = dfp.head(10)
sns.barplot(x = dfp10.Quantity, y = dfp10.Description, palette='deep')
plt.title('Top 10 Item Orders by Quantity Sold')
plt.show();


# In[7]:


from pyspark.sql.functions import round

dfnew = df.withColumn('revenue', df.Quantity*df.UnitPrice)
dfnew = dfnew.withColumn('revenue', round(dfnew.revenue, 2))
dfnew.show(10)


# In[8]:


dfrev = dfnew.groupBy('Description').agg({'revenue':'sum'})
dfrev = dfrev.withColumnRenamed('sum(revenue)', 'total_revenue')
dfrev = dfrev.withColumn('total_revenue', round(dfrev['total_revenue'], 2)).orderBy(dfrev.total_revenue, ascending=False)

dfrev.show(10)


# In[9]:


dfp = dfrev.toPandas()
dfp10 = dfp.head(10)
sns.barplot(x = dfp10.total_revenue, y = dfp10.Description, palette='deep')
plt.title('Top 10 Items by Revenue')
plt.show();


# ### Transitioning to SparkSQL for more thorough visualization. 

# In[10]:


df.createOrReplaceTempView('retail')


# In[11]:


res = spark.sql('SELECT * FROM retail LIMIT 10;')

res.show()


# In[12]:


res = spark.sql('SELECT Country, SUM(Quantity) AS total_sold FROM retail GROUP BY Country ORDER BY total_sold DESC LIMIT 20;')
res.show()


# In[13]:


dfp = res.toPandas().head(5)
sns.barplot(x=dfp.total_sold, y=dfp.Country, palette='deep')
plt.title('Top 5 Customer Countries by Quantity of Sales')
plt.show();


# In[14]:


def sql(statement):
    res = spark.sql(statement)
    res.show()
    return res


# In[15]:


res = sql("""WITH cte AS 
            (SELECT *, Quantity*UnitPrice AS revenue 
            FROM retail)
        SELECT Country, ROUND(SUM(revenue),2) AS total_revenue
        FROM cte
        GROUP BY Country
        ORDER BY total_revenue DESC
        LIMIT 20;""")


# In[16]:


dfp = res.toPandas().head(5)
sns.barplot(x=dfp.total_revenue, y=dfp.Country)
plt.title('Top 5 Customer Countries by Total Revenue')
plt.show();


# In[17]:


res = sql("""

WITH cte AS 
(SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
FROM retail)

SELECT Description, ROUND(SUM(revenue),2) AS total_revenue
FROM cte
WHERE Country = 'United Kingdom'
GROUP BY Description
ORDER BY total_revenue DESC
LIMIT 10;

""")


# In[18]:


dfp = res.toPandas()
sns.barplot(x=dfp.total_revenue, y=dfp.Description, palette='deep')
plt.title('Top Items Sold in UK By Total Revenue')
plt.show();


# ### How are these trends in the UK changing over time?

# In[19]:


res = sql("""

SELECT InvoiceDate
FROM retail
ORDER BY InvoiceDate
LIMIT 1;

""")


# In[20]:


res = sql("""

SELECT InvoiceDate
FROM retail
ORDER BY InvoiceDate DESC
LIMIT 1;

""")


# In[21]:


res = sql("""

WITH cte AS (
SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
FROM retail
),

    cte2 AS (
    SELECT Description, revenue, InvoiceDate,
        ROUND(SUM(revenue) OVER(PARTITION BY Description ORDER BY InvoiceDate 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),2) AS cumulative_rev
    FROM cte
    WHERE Country = 'United Kingdom'
    ),
    
    cte3 AS (
    SELECT 
                    Description AS item,                
                    EXTRACT(MONTH FROM InvoiceDate) AS month,
                    EXTRACT(YEAR FROM InvoiceDate) AS year,
                    cumulative_rev
    FROM cte2
    WHERE Description IN
        (SELECT Description
        FROM cte2
        GROUP BY Description
        HAVING MAX(cumulative_rev) > 75000)
)

SELECT item, month, year, AVG(cumulative_rev) AS monthly_cumulative_rev
FROM cte3
GROUP BY item, month, year
ORDER BY year, month

""")


# In[22]:


dfp = res.toPandas()
dfp.shape


# In[23]:


dfp['date'] = pd.to_datetime(dfp['year'].astype(str) + '-' + dfp['month'].astype(str) + '-01')

sns.lineplot(x=dfp.date, y=dfp.monthly_cumulative_rev, hue=dfp.item, alpha=0.6)
plt.show()


# In[24]:


dfp.head(50)


# In[25]:


sql("""

SELECT * 
FROM retail
WHERE Description = 'MEDIUM CERAMIC TOP STORAGE JAR'
LIMIT 5

""")


# In[26]:


res = sql("""

WITH cte AS (
SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
FROM retail
),

    cte2 AS (
    SELECT Description, revenue, InvoiceDate,
        ROUND(SUM(revenue) OVER(PARTITION BY Description ORDER BY InvoiceDate 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),2) AS cumulative_rev
    FROM cte
    WHERE Country = 'United Kingdom'
    ),
    
    cte3 AS (
    SELECT 
                    Description AS item,                
                    EXTRACT(MONTH FROM InvoiceDate) AS month,
                    EXTRACT(YEAR FROM InvoiceDate) AS year,
                    cumulative_rev
    FROM cte2
    WHERE Description IN
        (SELECT Description
        FROM cte2
        GROUP BY Description
        HAVING MAX(cumulative_rev) > 80000)
)

SELECT item, month, year, AVG(cumulative_rev) AS monthly_cumulative_rev
FROM cte3
GROUP BY item, month, year
ORDER BY year, month

""")


# In[27]:


dfp = res.toPandas()

dfp['date'] = pd.to_datetime(dfp['year'].astype(str) + '-' + dfp['month'].astype(str) + '-01')

plt.figure(figsize=(12,8))
sns.lineplot(x=dfp.date, y=dfp.monthly_cumulative_rev, hue=dfp.item, alpha=0.7)
sns.scatterplot(x='date', y='monthly_cumulative_rev', hue='item', data=dfp, marker='o', alpha=0.4, legend=False)

plt.title('Cumulative Revenue of Top 6 Items Sold in the UK')
plt.show();


# ### Two conclusions to draw from this: 
# ### 1. It looks like DOTCOM POSTAGE is on the rise, so we can continue to capitalize on that.
# ### 2. Even though Party Bunting has been a good revenue driver over the year, it looks like it's plateauing. Let's take a look at a few other countries to get a better idea.
# 
# ### As a reminder, the most profitable countries besides the UK are Netherlands, EIRE, France, and Germany.

# In[28]:


for country in ['Netherlands','EIRE','France','Germany']:
    
    print('*'*50)
    print(f'Generating SQL Query for {country}...')
    print('*'*50)
    
    res = sql(f"""

    WITH cte AS (
    SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
    FROM retail
    ),

        cte2 AS (
        SELECT Description, revenue, InvoiceDate,
            ROUND(SUM(revenue) OVER(PARTITION BY Description ORDER BY InvoiceDate 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),2) AS cumulative_rev
        FROM cte
        WHERE Country = '{country}'
        ),

        cte3 AS (
        SELECT 
                        Description AS item,                
                        EXTRACT(MONTH FROM InvoiceDate) AS month,
                        EXTRACT(YEAR FROM InvoiceDate) AS year,
                        cumulative_rev
        FROM cte2
        WHERE Description LIKE '%POSTAGE' 
            OR Description = 'PARTY BUNTING'
    )

    SELECT item, month, year, AVG(cumulative_rev) AS monthly_cumulative_rev
    FROM cte3
    GROUP BY item, month, year
    ORDER BY year, month

    """)
    
    dfp = res.toPandas()

    dfp['date'] = pd.to_datetime(dfp['year'].astype(str) + '-' + dfp['month'].astype(str) + '-01')

    plt.figure(figsize=(12,8))
    sns.lineplot(x=dfp.date, y=dfp.monthly_cumulative_rev, hue=dfp.item, alpha=0.7)
    sns.scatterplot(x='date', y='monthly_cumulative_rev', hue='item', data=dfp, marker='o', alpha=0.4, legend=False)

    plt.title(f'Cumulative Revenue of Top Items Sold in {country}')
    plt.show();


# In[29]:


for country in ['Netherlands','EIRE','France','Germany']:
    
    print('*'*50)
    print(f'Generating SQL Query for {country}...')
    print('*'*50)
    
    res = sql(f"""

    WITH cte AS (
    SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
    FROM retail
    ),

        cte2 AS (
        SELECT Description, revenue, InvoiceDate,
            ROUND(SUM(revenue) OVER(PARTITION BY Description ORDER BY InvoiceDate 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),2) AS cumulative_rev
        FROM cte
        WHERE Country = '{country}'
        ),

        cte3 AS (
        SELECT 
                        Description AS item,                
                        EXTRACT(MONTH FROM InvoiceDate) AS month,
                        EXTRACT(YEAR FROM InvoiceDate) AS year,
                        cumulative_rev
        FROM cte2
        WHERE Description IN
            (SELECT Description
            FROM cte2
            GROUP BY Description
            HAVING MAX(cumulative_rev) > 3000)
    )

    SELECT item, month, year, AVG(cumulative_rev) AS monthly_cumulative_rev
    FROM cte3
    GROUP BY item, month, year
    ORDER BY year, month

    """)
    
    dfp = res.toPandas()

    dfp['date'] = pd.to_datetime(dfp['year'].astype(str) + '-' + dfp['month'].astype(str) + '-01')

    plt.figure(figsize=(12,8))
    sns.lineplot(x=dfp.date, y=dfp.monthly_cumulative_rev, hue=dfp.item, alpha=0.7)
    sns.scatterplot(x='date', y='monthly_cumulative_rev', hue='item', data=dfp, marker='o', alpha=0.4, legend=False)

    plt.title(f'Cumulative Revenue of Top Items Sold in {country}')
    plt.show();


# In[30]:


for country in ['Netherlands','EIRE','France','Germany']:
    
    if country == 'Netherlands':
        value = 4000
    elif country == 'EIRE':
        value = 3000
    elif country == 'France':
        value= 2000
    elif country == 'Germany':
        value = 2000
        
    print('*'*50)
    print(f'Generating SQL Query for {country}...')
    print('*'*50)
    
    res = sql(f"""

    WITH cte AS (
    SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
    FROM retail
    ),

        cte2 AS (
        SELECT Description, revenue, InvoiceDate,
            ROUND(SUM(revenue) OVER(PARTITION BY Description ORDER BY InvoiceDate 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),2) AS cumulative_rev
        FROM cte
        WHERE Country = '{country}'
        ),

        cte3 AS (
        SELECT 
                        Description AS item,                
                        EXTRACT(MONTH FROM InvoiceDate) AS month,
                        EXTRACT(YEAR FROM InvoiceDate) AS year,
                        cumulative_rev
        FROM cte2
        WHERE Description IN
            (SELECT Description
            FROM cte2
            GROUP BY Description
            HAVING MAX(cumulative_rev) > {value})
    )

    SELECT item, month, year, AVG(cumulative_rev) AS monthly_cumulative_rev
    FROM cte3
    GROUP BY item, month, year
    ORDER BY year, month

    """)
    
    dfp = res.toPandas()

    dfp['date'] = pd.to_datetime(dfp['year'].astype(str) + '-' + dfp['month'].astype(str) + '-01')

    plt.figure(figsize=(12,8))
    sns.lineplot(x=dfp.date, y=dfp.monthly_cumulative_rev, hue=dfp.item, alpha=0.7)
    sns.scatterplot(x='date', y='monthly_cumulative_rev', hue='item', data=dfp, marker='o', alpha=0.4, legend=False)

    plt.title(f'Cumulative Revenue of Top Items Sold in {country}')
    plt.show();


# ### Definitely some interesting patterns in the other countries that have little to do with Party Bunting - but that rabbit night light seems to be taking off. 
# 
# ### What about individual customers? Who's our most profitable buyer, and what are they buying?

# In[31]:


res = sql("""


SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
FROM retail
ORDER BY revenue DESC
LIMIT 10;

""")


# In[32]:


res = sql("""

WITH cte AS (
SELECT *, ROUND(Quantity*UnitPrice, 2) AS revenue 
FROM retail
)

SELECT CustomerID, Country, ROUND(SUM(revenue),2) AS total_rev
FROM cte
WHERE CustomerID IS NOT NULL
GROUP BY CustomerID, Country
ORDER BY total_rev DESC
LIMIT 10;


""")


# In[33]:


res = sql("""

WITH customer_revenue AS (
    SELECT 
        CustomerID,
        Country,
        ROUND(SUM(Quantity * UnitPrice), 2) AS total_rev
    FROM retail
    WHERE CustomerID IS NOT NULL
    GROUP BY CustomerID, Country
    ORDER BY total_rev DESC
    LIMIT 1
),
    
    purchased as (
    SELECT 
        CustomerID, Description, UnitPrice,
        SUM(Quantity) as total_purchased 
    FROM retail
    WHERE 
        InvoiceNo NOT LIKE 'C%' AND
        CustomerID IN (SELECT CustomerID FROM customer_revenue)
    GROUP BY Description, CustomerID, UnitPrice
    ORDER BY CustomerID
)

SELECT *, ROUND(UnitPrice*total_purchased,2) AS total_revenue
FROM purchased
ORDER BY total_revenue DESC
LIMIT 5
;



""")


# In[34]:


dfp = res.toPandas()

plt.figure(figsize=(6, 10))
dfp.plot.pie(y='total_revenue', labels=dfp.Description, autopct='%1.2f%%', startangle=90, legend=False)
plt.axis('equal')
plt.ylabel('')
plt.title('Highest Revenue-Generating Items From Top Buyer')
plt.tight_layout()
plt.show();


# ### Let's make sure we keep hitting those numbers with deals on Round Snack Boxes!
