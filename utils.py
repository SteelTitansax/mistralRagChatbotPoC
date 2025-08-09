from contextlib import contextmanager
import sys
import os
import sqlite3


# --- Busqueda por wikipedia


def wikipedia_search(query):
    try:
        url = "https://es.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'extract' in data:
                return data['extract']
            else:
                return "No se encontró un resumen para esa consulta."
        else:
            return "No se encontró información en Wikipedia."
    except Exception as e:
        return f"Error accediendo a Wikipedia: {e}"

# --- Cargar documentos desde SQLite ---

def load_docs_from_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM documents")
    rows = cursor.fetchall()
    conn.close()

    docs = []
    for row in rows:
        docs.append({"page_content": row[2], "metadata": {"id": row[0], "title": row[1]}})
    return docs

# --- Función para silenciar stdout y stderr ---

@contextmanager
def suppress_output():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
