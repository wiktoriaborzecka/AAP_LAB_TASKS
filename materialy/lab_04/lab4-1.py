import sqlite3
import requests

# 1. Pobierz dane z API
response = requests.get("https://randomuser.me/api/?results=30")
users = response.json()["results"]

# 2. Stwórz tabelę (in-memory; podmień ":memory:" na "users.db" by zapisać na dysk)
conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE Users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name  TEXT,
        last_name   TEXT,
        email       TEXT,
        address     TEXT,
        age         INTEGER,
        gender      TEXT,
        country     TEXT
    )
""")

# 3. Wstaw dane z parametryzacją (chroni przed SQL injection)
rows = []
for u in users:
    loc = u["location"]
    street = loc["street"]
    address = f"{street['number']} {street['name']}, {loc['city']}"
    rows.append((
        u["name"]["first"],
        u["name"]["last"],
        u["email"],
        address,
        u["dob"]["age"],
        u["gender"],
        loc["country"],
    ))

cur.executemany("""
    INSERT INTO Users (first_name, last_name, email, address, age, gender, country)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", rows)
conn.commit()

# 4. Zapytania analityczne
print("Podział wg płci:")
for gender, count in cur.execute(
    "SELECT gender, COUNT(*) FROM Users GROUP BY gender"
):
    print(f"  {gender}: {count}")

avg_age = cur.execute("SELECT AVG(age) FROM Users").fetchone()[0]
print(f"\nŚredni wiek: {avg_age:.1f}")

country_count = cur.execute(
    "SELECT COUNT(DISTINCT country) FROM Users"
).fetchone()[0]
print(f"Liczba krajów: {country_count}")

print("\nKraje (malejąco):")
for country, count in cur.execute(
    "SELECT country, COUNT(*) FROM Users GROUP BY country ORDER BY COUNT(*) DESC"
):
    print(f"  {country}: {count}")

conn.close()