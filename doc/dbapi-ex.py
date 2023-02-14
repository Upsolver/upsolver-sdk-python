

#%%
# pip install upsolver-sdk-python
# pip install pandas
# pip install git+https://github.com/Upsolver/upsolver-sdk-python
# %%
import upsolver.dbapi as upsolver
# %%
con = upsolver.connect(token='..',api_url='..')
cur = upsolver.Cursor(con)
# %%
query = '''
        select
            customer.firstname,
            customer.lastname,
            nettotal as total,
            taxrate
        from default_glue_catalog.database_8edc49.orders_raw_data
        limit 5;
'''
res = cur.execute(query)
# %%
for r in res:
    print(r)
# %%
from beautifultable import BeautifulTable
# %%
print([c[0] for c in cur.description])
#%%
table = BeautifulTable()
table.column_headers = [c[0] for c in cur.description]
for r in res:
    table.append_row(r)
print(table)
# %%
import pandas as pd

df = pd.read_sql(query,con=con)
# %%
df.info()
# %%
df.head()
# %%
