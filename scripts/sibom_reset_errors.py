import sqlite3

def run():
    conn = sqlite3.connect('sibom/sibom.db', timeout=60)
    c = conn.cursor()
    c.execute("UPDATE normas SET procesado_llm = 0, notas_vigencia = NULL WHERE tipo = 'ordenanza' AND procesado_llm = -1")
    conn.commit()
    print(f"Reactivadas {c.rowcount} ordenanzas de procesado_llm = -1 a procesado_llm = 0")
    conn.close()

if __name__ == '__main__':
    run()
