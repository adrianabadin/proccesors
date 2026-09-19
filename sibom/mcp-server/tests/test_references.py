"""Pruebas para árbol de referencias normativas."""
from sibom_mcp.db import Database
from sibom_mcp.tools.references import get_references


def test_get_references_bidireccional(test_env):
    """Verifica referencias tanto hacia adelante como hacia atrás."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Norma 1 es modificada por Norma 2 y cita Ley 14.449
    refs1 = get_references(db, norma_id=1, direccion="ambas", profundidad=1)
    assert refs1["total_referencias"] >= 2
    
    # Verificar cita externa
    citas_externas = [r for r in refs1["referencias"] if r["destino"]["referencia_externa"]]
    assert len(citas_externas) >= 1
    assert "Ley 14.449" in citas_externas[0]["destino"]["referencia_externa"]


def test_get_references_ciclos_y_profundidad(test_env):
    """Verifica que referencias circulares terminen sin loop infinito."""
    db = Database(db_path=test_env["db_path"], index_path=test_env["index_path"])

    # Consultar con profundidad 3
    refs = get_references(db, norma_id=1, direccion="ambas", profundidad=3)
    # Debe terminar normalmente y tener longitud acotada
    assert refs["total_referencias"] >= 2
    assert refs["profundidad_maxima"] == 3
