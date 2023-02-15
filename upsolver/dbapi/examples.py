#%%
import upsolver.dbapi as upsolver
#%%
api_url = 'https://mt-api-prod.upsolver.com'
token = ''  # add token
command = "SELECT * FROM default_glue_catalog.database_053a79.orders_transformed_data LIMIT 10;"
file = "../test_scripts/select.usql"
#%%
conn = upsolver.connect(token, api_url)
cursor = conn.cursor()
#%%
s3_command = "CREATE S3 CONNECTION upsolver_s3 "\
                "AWS_ROLE = 'arn:aws:iam::949275490180:role/upsolver_samples_role' "\
                "EXTERNAL_ID = 'SAMPLES' " \
                "READ_ONLY = TRUE;"
s3_del_command = "DROP CONNECTION upsolver_s3;"
#%%
# delete the connection just in case it was previously created
res = cursor.execute(s3_del_command)
for line in res:
    print(line)
#%%
res = cursor.execute(s3_command)
for line in res:
    print(line)
#%%
print('Execute result:')
result1 = cursor.execute(command)
print(type(result1)) # Should be generator
#%%
rowcount = cursor.rowcount
print(f'Row count: {rowcount}')
#%%
print('Description:')
description = cursor.description
for line in description:
    print(line[0], line[1], '- type check valid' if upsolver.STRING == line[1] else '- type check invalid')
#%%
print('Fetch one result:')
result2 = cursor.fetchone()
print(result2)
#%%
print('Fetch many result:')
cursor.arraysize = 3
result3 = cursor.fetchmany()
for line in result3:
    print(line)
#%%
print('Fetch all result:')
result4 = cursor.fetchall()
for line in result4:
    print(line)
#%%
print('Fetch one on empty:')
result5 = cursor.fetchone()
print(result5)
#%%
print('Fetch many on empty:')
result6 = cursor.fetchmany()
print(result6)
#%%
print('Execute from file result:')
result7 = cursor.executefile(file)
for line in result7:
    print(line)
#%%
cursor.close()
try:
    result7 = cursor.execute(command)
except BaseException as e:
    print('Caught error on closed cursor')
#%%
conn.close()
try:
    new_cursor = conn.cursor()
except BaseException as e:
    print('Caught error on closed connection')
# %%
