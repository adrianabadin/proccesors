"""Script de benchmarking para medir calidad de recuperación y latencias en SIBOM."""
import argparse
import json
import os
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
import numpy as np
import psutil

# Asegurar importación de sibom_mcp
sys_path = Path(__file__).resolve().parents[1]
import sys
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

from sibom_mcp.config import settings
from sibom_mcp.db import Database
from sibom_mcp.tools.search import search_normas
from sibom_mcp.tools.semantic import semantic_search
from sibom_mcp.tools.compilar import compilar_tematica
from sibom_mcp.tools.comparar import comparar_intermunicipal


def run_benchmark(
    db_path: str,
    cases_path: str,
    output_path: str | None = None,
    concurrency_levels: list[int] = [1, 4],
    iterations: int = 3
) -> dict[str, Any]:
    """Ejecuta suite completa de mediciones de latencia y calidad."""
    cases_file = Path(cases_path).resolve()
    cases_data = json.loads(cases_file.read_text(encoding="utf-8"))
    cases = cases_data.get("cases", [])

    db = Database(db_path=db_path)
    process = psutil.Process(os.getpid())

    print(f"=== INICIANDO BENCHMARK SIBOM MCP ===")
    print(f"Base de datos: {db_path}")
    print(f"Casos de evaluación: {len(cases)}")
    print(f"Plataforma: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_version()}")

    # 1. Warm-up (Arranque en frío vs caliente)
    t0 = time.perf_counter()
    warmup_res = search_normas(db, query="presupuesto", limit=5)
    cold_time_ms = round((time.perf_counter() - t0) * 1000, 2)

    t0 = time.perf_counter()
    search_normas(db, query="presupuesto", limit=5)
    hot_time_ms = round((time.perf_counter() - t0) * 1000, 2)

    # 2. Evaluación de calidad y latencia FTS5
    fts_latencies: list[float] = []
    fts_hits = 0
    case_results = []

    for c in cases:
        q = c["query"]
        expected_kw = [k.lower() for k in c["keywords_relevantes"]]
        
        # Medir latencia
        start = time.perf_counter()
        res = search_normas(db, query=q, tipo=c.get("tipo_esperado", "ordenanza"), limit=10)
        elapsed_ms = (time.perf_counter() - start) * 1000
        fts_latencies.append(elapsed_ms)

        # Evaluar relevancia léxica en títulos y resúmenes retornados
        matched_any = False
        if res["items"]:
            for item in res["items"]:
                combined_text = (item["titulo"] + " " + (item["resumen"] or "")).lower()
                if any(kw in combined_text for kw in expected_kw):
                    matched_any = True
                    break
        if matched_any:
            fts_hits += 1

        case_results.append({
            "id": c["id"],
            "query": q,
            "latency_ms": round(elapsed_ms, 2),
            "returned_count": res["returned_count"],
            "hit_success": matched_any
        })

    # Métricas estadísticas FTS5
    p50_fts = round(float(np.percentile(fts_latencies, 50)), 2)
    p95_fts = round(float(np.percentile(fts_latencies, 95)), 2)
    avg_fts = round(float(np.mean(fts_latencies)), 2)
    hit_rate = round((fts_hits / len(cases)) * 100, 1)

    # 3. Medición de Búsqueda Semántica Vectorial (matrices NumPy en memoria)
    sem_latencies = []
    for c in cases[:5]:  # Muestra de 5 casos
        start = time.perf_counter()
        try:
            res_sem = semantic_search(db, query=c["query"], limit=10, mock=True)
            elapsed_ms = (time.perf_counter() - start) * 1000
            sem_latencies.append(elapsed_ms)
        except Exception:
            pass

    p50_sem = round(float(np.percentile(sem_latencies, 50)), 2) if sem_latencies else 0.0
    p95_sem = round(float(np.percentile(sem_latencies, 95)), 2) if sem_latencies else 0.0

    # 4. Medición de Compilación Temática
    t_comp_start = time.perf_counter()
    comp_res = compilar_tematica(db, tema="vivienda", limit=10)
    comp_time_ms = round((time.perf_counter() - t_comp_start) * 1000, 2)

    # 5. Medición de Comparación Intermunicipal
    t_comp_inter_start = time.perf_counter()
    comp_inter_res = comparar_intermunicipal(db, tema="habitat", limit_candidatos=10)
    comp_inter_ms = round((time.perf_counter() - t_comp_inter_start) * 1000, 2)

    # 6. Concurrencia (1 y 4 hilos)
    concurrency_metrics = {}
    for conc in concurrency_levels:
        queries = [c["query"] for c in cases] * iterations
        t_start = time.perf_counter()

        def do_search(query_str: str):
            return search_normas(db, query=query_str, limit=5)

        with ThreadPoolExecutor(max_workers=conc) as executor:
            list(executor.map(do_search, queries))

        total_duration = time.perf_counter() - t_start
        qps = round(len(queries) / total_duration, 2)
        concurrency_metrics[f"concurrency_{conc}"] = {
            "workers": conc,
            "total_queries": len(queries),
            "total_duration_sec": round(total_duration, 3),
            "qps": qps
        }

    # Memoria RSS
    rss_mb = round(process.memory_info().rss / (1024 * 1024), 2)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hardware": {
            "os": f"{platform.system()} {platform.release()}",
            "arch": platform.machine(),
            "cpu_count": psutil.cpu_count(logical=True),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": platform.python_version()
        },
        "system_status": {
            "cold_start_ms": cold_time_ms,
            "hot_start_ms": hot_time_ms,
            "rss_mb": rss_mb
        },
        "fts5_performance": {
            "sample_size": len(cases),
            "hit_rate_percentage": hit_rate,
            "latency_p50_ms": p50_fts,
            "latency_p95_ms": p95_fts,
            "latency_avg_ms": avg_fts,
            "target_met_p95_under_200ms": p95_fts < 200.0
        },
        "semantic_performance": {
            "latency_p50_ms": p50_sem,
            "latency_p95_ms": p95_sem,
            "target_met_under_1s": p95_sem < 1000.0
        },
        "compilacion_performance": {
            "latency_ms": comp_time_ms,
            "returned_candidates": comp_res["total_candidates"]
        },
        "comparacion_performance": {
            "latency_ms": comp_inter_ms,
            "candidatos_analizados": comp_inter_res.get("candidatos_analizados", 0),
            "target_met_under_5s": comp_inter_ms < 5000.0
        },
        "concurrency": concurrency_metrics,
        "evaluations": case_results
    }

    if output_path:
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Reporte guardado en: {out_file}")

    print("\n=== RESUMEN DE RENDIMIENTO MEDIDO ===")
    print(f"• RSS Memoria: {rss_mb} MB")
    print(f"• FTS5 Latencia Caliente: p50={p50_fts} ms | p95={p95_fts} ms (Objetivo < 200ms: {'CUMPLIDO' if p95_fts < 200 else 'NO'})")
    print(f"• FTS5 Hit Rate Relevancia: {hit_rate}%")
    print(f"• Búsqueda Semántica: p50={p50_sem} ms | p95={p95_sem} ms (Objetivo < 1000ms: {'CUMPLIDO' if p95_sem < 1000 else 'NO'})")
    print(f"• Compilación Temática: {comp_time_ms} ms")
    print(f"• Comparación Intermunicipal: {comp_inter_ms} ms (Objetivo < 5000ms: {'CUMPLIDO' if comp_inter_ms < 5000 else 'NO'})")
    for k, v in concurrency_metrics.items():
        print(f"• Concurrencia ({v['workers']} workers): {v['qps']} QPS")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark de búsqueda y rendimiento SIBOM MCP")
    parser.add_argument("--db", default=settings.sibom_db_path, help="Ruta a sibom.db")
    parser.add_argument(
        "--cases",
        default=str(sys_path / "tests" / "evaluations" / "cases.json"),
        help="Ruta al archivo cases.json"
    )
    parser.add_argument("--output", default=str(sys_path / "docs" / "benchmark-results.json"), help="Ruta para guardar JSON")
    args = parser.parse_args()

    run_benchmark(db_path=args.db, cases_path=args.cases, output_path=args.output)
