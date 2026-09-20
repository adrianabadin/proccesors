import sqlite3

conn = sqlite3.connect('sibom/sibom.db')
c = conn.cursor()

c.execute('SELECT count(1) FROM normas')
total_normas = c.fetchone()[0]

c.execute('SELECT count(1) FROM normas WHERE procesado_llm = 1')
enriquecidas_total = c.fetchone()[0]

c.execute("SELECT count(1) FROM normas WHERE tipo = 'ordenanza'")
total_ordenanzas = c.fetchone()[0]

c.execute("SELECT count(1) FROM normas WHERE tipo = 'ordenanza' AND procesado_llm = 1")
enriquecidas_ord = c.fetchone()[0]

c.execute("SELECT count(1) FROM normas WHERE tipo = 'ordenanza' AND procesado_llm = -1")
errores_ord = c.fetchone()[0]

c.execute('SELECT count(1) FROM articulos')
total_arts = c.fetchone()[0]

c.execute('SELECT count(1) FROM referencias_normativas')
total_refs = c.fetchone()[0]

c.execute('SELECT estado, count(1) FROM normas GROUP BY estado')
estados_normas = dict(c.fetchall())

c.execute('SELECT estado, count(1) FROM articulos GROUP BY estado')
estados_arts = dict(c.fetchall())

c.execute('''
    SELECT count(DISTINCT codigo_localidad)
    FROM normas
    WHERE tipo = 'ordenanza'
''')
distritos_totales = c.fetchone()[0]

c.execute('''
    SELECT codigo_localidad, localidad, count(1) as total,
           sum(CASE WHEN procesado_llm = 1 THEN 1 ELSE 0 END) as ok,
           sum(CASE WHEN procesado_llm != 1 THEN 1 ELSE 0 END) as pendientes
    FROM normas
    WHERE tipo = 'ordenanza'
    GROUP BY codigo_localidad
    HAVING pendientes > 0
    ORDER BY pendientes DESC
''')
pendientes_por_loc = c.fetchall()

distritos_cerrados = distritos_totales - len(pendientes_por_loc)

print(f"Total Normas en DB: {total_normas:,}")
print(f"Total Enriquecidas (todas): {enriquecidas_total:,} ({enriquecidas_total/total_normas*100:.2f}%)")
print(f"Total Ordenanzas: {total_ordenanzas:,}")
print(f"Ordenanzas Enriquecidas: {enriquecidas_ord:,} ({enriquecidas_ord/total_ordenanzas*100:.2f}%)")
print(f"Ordenanzas Pendientes: {total_ordenanzas - enriquecidas_ord:,}")
print(f"Ordenanzas Errores (-1): {errores_ord}")
print(f"Artículos estructurados: {total_arts:,}")
print(f"Referencias normativas: {total_refs:,}")
print(f"Distritos con ordenanzas: {distritos_totales}")
print(f"Distritos 100% cerrados: {distritos_cerrados} ({distritos_cerrados/distritos_totales*100:.1f}%)")
print(f"Distritos pendientes: {len(pendientes_por_loc)}")
print("\nDetalle de distritos con ordenanzas pendientes:")
for loc in pendientes_por_loc:
    pct = (loc[3] / loc[2]) * 100
    print(f"  [{loc[0]}] {loc[1]}: {loc[4]} pendientes ({pct:.1f}% completo, {loc[3]}/{loc[2]})")
