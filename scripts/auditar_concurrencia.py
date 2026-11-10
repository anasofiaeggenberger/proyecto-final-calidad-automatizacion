"""Reproduce carreras con intercalados controlados; no modifica el dominio.

Devuelve 1 si detecta una inconsistencia. No forma parte de la suite de aceptación.
"""

import inspect
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain.patient_queue import PatientQueue  # noqa: E402


def interleave(method, needle, operation):
    source, start = inspect.getsourcelines(method)
    line = start + next(i for i, text in enumerate(source) if needle in text)
    barrier = threading.Barrier(2, timeout=5)
    def trace(frame, event, arg):
        if frame.f_code is method.__code__ and event == "line" and frame.f_lineno == line:
            barrier.wait()
        return trace
    def worker(index):
        sys.settrace(trace)
        try:
            return {"result": operation(index)}
        except Exception as error:
            return {"error": type(error).__name__}
        finally:
            sys.settrace(None)
    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(worker, range(2)))


def main():
    queue = PatientQueue()
    created = interleave(
        PatientQueue.enqueue, "self._next_id +=",
        lambda i: queue.enqueue(f"Paciente {i}", 3).id,
    )
    ordered = queue.list_ordered()
    duplicate_ids = len({p.id for p in ordered}) != len(ordered)
    duplicate_arrivals = len({p.orden_llegada for p in ordered}) != len(ordered)
    queue = PatientQueue()
    patient = queue.enqueue("Paciente", 1)
    removed = interleave(
        PatientQueue.remove_by_id, "removed = self._heap.pop",
        lambda _: queue.remove_by_id(patient.id),
    )
    queue = PatientQueue()
    queue.enqueue("Paciente", 1)
    attended = interleave(
        PatientQueue.attend_next, "return heapq.heappop",
        lambda _: queue.attend_next(),
    )
    result = {
        "tecnica": "dos threads reales; barrera mediante sys.settrace antes de operaciones no atomicas",
        "altas": created, "ids_duplicados": duplicate_ids,
        "llegadas_duplicadas": duplicate_arrivals,
        "prioridades_ordenadas": [p.prioridad for p in ordered] == sorted(p.prioridad for p in ordered),
        "fifo_univoco": not duplicate_arrivals,
        "eliminacion": [x.get("error", "ok") for x in removed],
        "atencion": [x.get("error", "ok") for x in attended],
    }
    print(json.dumps(result, indent=2))
    return int(duplicate_ids or duplicate_arrivals or any("error" in x for x in removed + attended))


if __name__ == "__main__":
    raise SystemExit(main())
