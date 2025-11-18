import chromadb

client = chromadb.Client()
cols = client.list_collections()
print('Collections:', [c.name for c in cols])
try:
    col = client.get_collection('acebuddy_kb')
    res = col.get()
    docs = res.get('documents', [])
    print('acebuddy_kb docs:', len(docs))
except Exception as e:
    print('Could not access acebuddy_kb:', e)
