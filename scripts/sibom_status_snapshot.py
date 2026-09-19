import sqlite3

def run():
    conn = sqlite3.connect('sibom/sibom.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(1), SUM(CASE WHEN procesado_llm=1 THEN 1 ELSE 0 END) FROM normas WHERE tipo='ordenanza'")
    tot_o, enr_o = c.fetchone()
    c.execute("SELECT COUNT(1), SUM(CASE WHEN procesado_llm=1 THEN 1 ELSE 0 END) FROM normas")
    tot_n, enr_n = c.fetchone()
    c.execute("SELECT COUNT(1) FROM articulos")
    arts = c.fetchone()[0]
    c.execute("SELECT COUNT(1) FROM referencias_normativas")
    refs = c.fetchone()[0]

    print(f"TOTAL NORMAS EN BD: {tot_n:,} | ENRIQUECIDAS LLM: {enr_n:,} ({enr_n/tot_n*100:.2f}%)")
    print(f"ORDENANZAS PBA: {enr_o:,} / {tot_o:,} ({enr_o/tot_o*100:.2f}%) - FALTAN: {tot_o - enr_o:,}")
    print(f"ARTICULOS ESTRUCTURADOS: {arts:,} | REFERENCIAS NORMATIVAS: {refs:,}")
    conn.close()

if __name__ == '__main__':
    run()
