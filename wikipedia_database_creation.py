import sqlite3
import requests
import time

DB_NAME = 'data.db'
MAX_ITEMS = 1500  # cantidad de artículos a obtener por ejecución

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL
)
''')

API_RANDOM_URL = "https://es.wikipedia.org/api/rest_v1/page/random/summary"

# Palabras clave para filtrar artículos relevantes en español
keywords = [
    "España", "español", "Madrid", "Cataluña", "literatura", "ciencia", "tecnología",
    "ingeniería", "científico", "investigación", "universidad", "premio Nobel",
    "artículo", "historia", "biología", "física", "química", "matemáticas",
    "informática", "software", "hardware", "robot", "mecánica", "electricidad",
    "energía", "ecología", "nanotecnología", "IA", "inteligencia artificial",
    "desarrollo", "innovación", "automática", "electrónica"
]

def es_relevante(texto):
    texto = texto.lower()
    return any(k.lower() in texto for k in keywords)

docs = []
intentos = 0
print(f"Obteniendo hasta {MAX_ITEMS} artículos aleatorios relevantes de Wikipedia en español...")

while len(docs) < MAX_ITEMS and intentos < MAX_ITEMS * 10:
    try:
        res = requests.get(API_RANDOM_URL, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        data = res.json()
        title = data.get("title", "").strip()
        extract = data.get("extract", "").strip()
        
        if title and extract and es_relevante(extract):
            docs.append((title, extract))
            print(f"✅ {len(docs)} - {title}")
        else:
            print(f"❌ Rechazado (no relevante): {title}")
        
        intentos += 1
        time.sleep(0.2)  # para no saturar la API
        
    except Exception as e:
        print(f"Error en petición: {e}")
        time.sleep(1)
        intentos += 1

if docs:
    cursor.executemany('INSERT OR IGNORE INTO documents (title, content) VALUES (?, ?)', docs)
    conn.commit()
    print(f"\n💾 Insertados {len(docs)} artículos nuevos en '{DB_NAME}'.")
else:
    print("No se obtuvieron artículos relevantes.")

conn.close()
