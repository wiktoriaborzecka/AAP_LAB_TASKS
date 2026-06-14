from pymongo import MongoClient
import requests

# 1. Połącz z MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client.lab4
networks = db["networks"]

# Czyścimy kolekcję, by ponowne uruchomienia nie duplikowały danych
networks.delete_many({})

# 2. Pobierz dane z API (z nagłówkiem — GeckoTerminal wymaga Accept)
response = requests.get(
    "https://api.geckoterminal.com/api/v2/networks",
    headers={"Accept": "application/json"},
)
data = response.json()["data"]

# 3. Wstaw dokumenty (Mongo przyjmuje listę dictów bezpośrednio)
networks.insert_many(data)
print(f"Wstawiono {networks.count_documents({})} dokumentów")

# 4. Agregacja — ile sieci per typ
pipeline = [
    {"$group": {"_id": "$type", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
print("\nLiczba sieci per typ:")
for doc in networks.aggregate(pipeline):
    print(f"  {doc['_id']}: {doc['count']}")

client.close()