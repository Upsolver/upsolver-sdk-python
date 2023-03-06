# Using Upsolver with DBAPI in python

## What is Upsolver

[Upsolver](https://upsolver.com) enables you to use familiar SQL syntax to quickly build and deploy data pipelines, powered by a stream processing engine designed for cloud data lakes.

## SQLake

[SQLake](https://docs.upsolver.com/sqlake) is Upsolvers new UI and SQL console allowing to execute commands and monitor pipelines in the UI. It also includes freee trial and access to variety of examples and tutorials.


## What is DB API

Python's DB API 2.0 is defined in [pep-249](https://peps.python.org/pep-0249/). It defines an abstract API for connecting and working with databases in Python. Many python libraries support DB API v2.0 natively, for example `pandas`, `SQLAlchemy`, and more.

## Getting started

### Install Upsolver SDK for Python

To use Upsolver SDK for Python you'll need Python interpreter of version greater than 3.7 

```bash
# For release version:
pip install upsolver-sdk-python
# for latest development version
pip install git+https://github.com/Upsolver/upsolver-sdk-python
```

### Register Upsolver account

To register just navigate to [SQL Lake Sign Up form](https://sqlake.upsolver.com/signup). You'll have access to SQL workbench with examples and tutorials after completing the registration.

### Create API token

After login navigate to "[Settings](https://sqlake.upsolver.com/Settings)" and then to "[API Tokens](https://sqlake.upsolver.com/Settings/api-tokens)"

You will need API token and API Url to access Upsolver programatically.

![API Tokens screen](https://github.com/Upsolver/upsolver-sdk-python/raw/build_package/doc/img/APITokens-m.png)

Then click "Generate" new token and save it for future use.

## Connections and cursors

Connecting to SQLake using the python SDK involves a few simple steps:

- create a `Connection`
- create a `Cursor`
- execute query

```python
# import upsolver DB API
import upsolver.dbapi as upsolver

# Configure your token and URL
token=...
api_url=...

#create connection and cursor
con = upsolver.connect(token=token,api_url=api_url)
cur = upsolver.Cursor(con)

# execute query
res = cur.execute('''
        select
            customer.firstname,
            customer.lastname,
            nettotal as total,
            taxrate
        from default_glue_catalog.database_8edc49.orders_raw_data
        limit 5;
''')

# now we can iterate the results
for r in res:
    print(r)

['John', 'Williams', '415.04', '0.12']
['Richard', 'Miller', '842.1', '0.12']
['Charles', 'Martinez', '1994.6', '0.12']
['Roy', 'Hughes', '0.0', '0.12']
['Teresa', 'Reed', '1080.72', '0.12']
```

We can use libraries to print the pretty-print the results:

```python
from beautifultable import BeautifulTable

res = cur.execute('''
        select
            customer.firstname,
            customer.lastname,
            nettotal as total,
            taxrate
        from default_glue_catalog.database_8edc49.orders_raw_data
        limit 5;
''')

table = BeautifulTable()
table.column_headers = [c[0] for c in cur.description]
for r in res:
    table.append_row(r)
print(table)
+-----------+----------+---------+---------+
| firstname | lastname |  total  | taxrate |
+-----------+----------+---------+---------+
| Samantha  |  Green   | 607.53  |  0.12   |
+-----------+----------+---------+---------+
| Virginia  |  Evans   | 270.02  |  0.12   |
+-----------+----------+---------+---------+
|  Abigail  |  Watson  | 1194.39 |  0.12   |
+-----------+----------+---------+---------+
|    Ann    |  Bailey  | 1655.7  |  0.12   |
+-----------+----------+---------+---------+
|   Kelly   | Edwards  | 1368.78 |  0.12   |
+-----------+----------+---------+---------+
```

Note: The examples above use the sample data provided by the template "S3 to Athena" in SQLake

## We can use pandas too

`pandas` is very popular library for data maipulations.
It's possible to rewrite the above example with pandas

```python
import pandas as pd

df = pd.read_sql(query,con=con)
df.info()
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 5 entries, 0 to 4
Data columns (total 4 columns):
 #   Column     Non-Null Count  Dtype 
---  ------     --------------  ----- 
 0   firstname  5 non-null      object
 1   lastname   5 non-null      object
 2   total      5 non-null      object
 3   taxrate    5 non-null      object
dtypes: object(4)
```

![`df.head()`](https://github.com/Upsolver/upsolver-sdk-python/raw/build_package/doc/img/df.head-m.jpeg)

## Upsolver SQL

See Upsolver's [SQL Command Reference](https://docs.upsolver.com/sqlake/sql-command-reference) for the supported SQL commands and syntax.

## Further reading

[upsolver.com](https://upsolver.com)

[Documentation](https://docs.upsolver.com/sqlake/sql-command-reference) of Upsolver SQL

[upsolver-sdk-python](https://github.com/Upsolver/upsolver-sdk-python) - GitHub repository with upsolver SDK for Python language

[SQLake workbench](https://sqlake.upsolver.com/) main page

[Python examples from this README](doc/dbapi-ex.py)
