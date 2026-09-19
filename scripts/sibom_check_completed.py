import sqlite3

def run():
    conn = sqlite3.connect('sibom/sibom.db')
    c = conn.cursor()
    c.execute('''
        SELECT 
            codigo_localidad,
            localidad,
            SUM(CASE WHEN LOWER(tipo) LIKE '%ordenanza%' THEN 1 ELSE 0 END) as tot_o,
            SUM(CASE WHEN LOWER(tipo) LIKE '%ordenanza%' AND procesado_llm = 1 THEN 1 ELSE 0 END) as enr_o
        FROM normas
        GROUP BY codigo_localidad, localidad
        HAVING tot_o > 0
        ORDER BY (CAST(enr_o AS FLOAT) / tot_o) DESC, tot_o DESC
    ''')
    rows = c.fetchall()
    completados = []
    pendientes = []
    for cid, loc, tot, enr in rows:
        pct = (enr / tot * 100) if tot > 0 else 0
        if tot == enr:
            completados.append((cid, loc, tot))
        else:
            pendientes.append((cid, loc, tot, enr, pct, tot - enr))
    
    print(f"=== MUNICIPIOS CON ORDENANZAS 100% CERRADAS ({len(completados)}) ===")
    for cid, loc, tot in completados:
        print(f"  [OK] [{cid:3d}] {loc:<25} : {tot} ordenanzas")
    
    print(f"\n=== MUNICIPIOS CON ORDENANZAS EN CURSO / PENDIENTES ({len(pendientes)}) ===")
    for cid, loc, tot, enr, pct, restan in pendientes:
        print(f"  [..] [{cid:3d}] {loc:<25} : {enr}/{tot} ({pct:5.1f}%) - Faltan: {restan}")

    conn.close()

if __name__ == '__main__':
    run()
