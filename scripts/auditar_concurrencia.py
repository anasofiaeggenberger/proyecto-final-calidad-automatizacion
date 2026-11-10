"""Comprueba unicidad y retiros concurrentes tras la corrección del dominio."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.patient_queue import PatientQueue  # noqa: E402


def parallel(operation, count=64):
    barrier = Barrier(16, timeout=5)
    def run(index):
        if index < 16:
            barrier.wait()
        return operation(index)
    with ThreadPoolExecutor(max_workers=16) as pool:
        return list(pool.map(run, range(count)))


def main():
    queue = PatientQueue()
    created = parallel(lambda i: queue.enqueue(f"P{i}", i % 5 + 1), 400)
    expected = sorted(created, key=lambda p: (p.prioridad, p.orden_llegada))
    result = {
        "tecnica": "16 threads; altas, lecturas y retiros reales sobre una cola aislada",
        "pacientes": len(created),
        "ids_unicos": len({p.id for p in created}) == 400,
        "llegadas_unicas": sorted(p.orden_llegada for p in created) == list(range(400)),
        "prioridad_fifo": queue.list_ordered() == expected,
    }
    for action in ("atender", "eliminar_id", "eliminar_nombre"):
        queue = PatientQueue()
        patient = queue.enqueue("Paciente", 1)
        operations = {
            "atender": queue.attend_next,
            "eliminar_id": lambda: queue.remove_by_id(patient.id),
            "eliminar_nombre": lambda: queue.remove_by_name(patient.nombre),
        }
        retired = parallel(lambda _: operations[action]())
        result[action] = retired.count(patient) == 1 and retired.count(None) == 63
    print(json.dumps(result, indent=2))
    return int(not all(value for key, value in result.items() if key not in ("tecnica", "pacientes")))


if __name__ == "__main__":
    raise SystemExit(main())
