import sqlite3

conn = sqlite3.connect('sibom/sibom.db')
c = conn.cursor()

c.execute('''
    SELECT 
        codigo_localidad,
        localidad,
        COUNT(*) as total_normas,
        SUM(CASE WHEN procesado_llm = 1 THEN 1 ELSE 0 END) as enr_normas,
        SUM(CASE WHEN LOWER(tipo) LIKE '%ordenanza%' THEN 1 ELSE 0 END) as total_ords,
        SUM(CASE WHEN LOWER(tipo) LIKE '%ordenanza%' AND procesado_llm = 1 THEN 1 ELSE 0 END) as enr_ords,
        SUM(CASE WHEN LOWER(tipo) LIKE '%decreto%' THEN 1 ELSE 0 END) as total_decs,
        SUM(CASE WHEN LOWER(tipo) LIKE '%decreto%' AND procesado_llm = 1 THEN 1 ELSE 0 END) as enr_decs
    FROM normas
    GROUP BY codigo_localidad, localidad
    ORDER BY (CAST(enr_ords AS FLOAT) / CASE WHEN total_ords > 0 THEN total_ords ELSE 1 END) DESC, total_normas DESC
''')

rows = c.fetchall()

print(f"{'ID':>4} | {'Municipio':<25} | {'Tot Normas':>10} | {'Enr Normas':>10} | {'% Tot':>6} | {'Tot Ords':>8} | {'Enr Ords':>8} | {'% Ords':>7} | {'Tot Decs':>8} | {'Enr Decs':>8} | {'% Decs':>7}")
print("-" * 125)

for r in rows:
    cid, loc, tot_n, enr_n, tot_o, enr_o, tot_d, enr_d = r
    pct_n = (enr_n / tot_n * 100) if tot_n > 0 else 0
    pct_o = (enr_o / tot_o * 100) if tot_o > 0 else 0
    pct_d = (enr_d / tot_d * 100) if tot_d > 0 else 0
    print(f"{cid:4d} | {loc:<25} | {tot_n:10d} | {enr_n:10d} | {pct_n:5.1f}% | {tot_o:8d} | {enr_o:8d} | {pct_o:6.1f}% | {tot_d:8d} | {enr_d:8d} | {pct_d:6.1f}%")

conn.close()
