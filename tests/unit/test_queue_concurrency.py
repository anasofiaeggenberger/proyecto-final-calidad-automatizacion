"""Regresiones de concurrencia de la cola, sin Flask ni estado compartido."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from domain.patient_queue import PatientQueue


def parallel(function, size=32):
    barrier = Barrier(min(size, 16), timeout=5)
    def worker(i):
        if i < 16:
            barrier.wait()
        return function(i)
    with ThreadPoolExecutor(max_workers=16) as pool:
        return list(pool.map(worker, range(size)))


def test_altas_concurrentes_tienen_ids_y_llegadas_unicos_y_fifo():
    queue = PatientQueue()
    created = parallel(lambda i: queue.enqueue(f"P{i}", i % 5 + 1), 400)
    assert len({p.id for p in created}) == 400
    assert sorted(p.orden_llegada for p in created) == list(range(400))
    expected = sorted(created, key=lambda p: (p.prioridad, p.orden_llegada))
    assert queue.list_ordered() == expected
    assert [queue.attend_next() for _ in created] == expected
    assert queue.is_empty()


@pytest.mark.parametrize("action", ["attend", "id", "name"])
def test_un_paciente_solo_puede_ser_retirado_una_vez(action):
    queue = PatientQueue()
    patient = queue.enqueue("Mismo nombre", 1)
    methods = {
        "attend": queue.attend_next,
        "id": lambda: queue.remove_by_id(patient.id),
        "name": lambda: queue.remove_by_name(patient.nombre),
    }
    results = parallel(lambda _: methods[action]())
    assert results.count(patient) == 1
    assert results.count(None) == 31
    assert queue.list_ordered() == []


def test_lecturas_y_mutaciones_concurrentes_conservan_todos_los_pacientes():
    queue = PatientQueue()
    def worker(i):
        created, removed = [], []
        for j in range(30):
            patient = queue.enqueue(f"P{i}-{j}", j % 5 + 1)
            created.append(patient)
            snapshot = queue.list_ordered()
            assert snapshot == sorted(snapshot)
            queue.peek()
            len(queue)
            queue.is_empty()
            retired = queue.attend_next() if j % 2 else queue.remove_by_name(patient.nombre)
            if retired:
                removed.append(retired)
        return created, removed
    batches = parallel(worker, 32)
    created = [p for adds, _ in batches for p in adds]
    removed = [p for _, retired in batches for p in retired]
    remaining = queue.list_ordered()
    assert len({p.id for p in created}) == len(created) == 960
    assert len({p.id for p in removed}) == len(removed)
    assert {p.id for p in removed}.isdisjoint(p.id for p in remaining)
    assert {p.id for p in created} == {p.id for p in removed + remaining}

def test_una_alta_incompleta_bloquea_la_siguiente(monkeypatch):
    """Fuerza el intercalado que antes duplicaba IDs, sin alterar el dominio."""
    from concurrent.futures import TimeoutError
    from threading import Event
    from domain.patient import Patient

    entered, release, second_started = Event(), Event(), Event()
    def construct(**kwargs):
        patient = Patient(**kwargs)
        if kwargs["nombre"] == "primero":
            entered.set()
            assert release.wait(5)
        return patient
    monkeypatch.setattr("domain.patient_queue.Patient", construct)
    queue = PatientQueue()
    def second():
        second_started.set()
        return queue.enqueue("segundo", 1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(queue.enqueue, "primero", 1)
        try:
            assert entered.wait(5)
            other = pool.submit(second)
            assert second_started.wait(5)
            with pytest.raises(TimeoutError):
                other.result(timeout=0.1)
        finally:
            release.set()
        patients = [first.result(timeout=5), other.result(timeout=5)]
    assert [p.id for p in patients] == ["p-0001", "p-0002"]
    assert [p.orden_llegada for p in patients] == [0, 1]
