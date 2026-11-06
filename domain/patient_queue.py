"""Cola de prioridad aislable para pacientes hospitalarios."""

import heapq

from .patient import Patient


class PatientQueue:
    """Mantiene pacientes ordenados por prioridad y orden de llegada.

    Cada instancia tiene sus propios contadores de IDs y de llegada. Al
    eliminar un paciente, ambos contadores continúan avanzando para evitar
    reutilizar identificadores u órdenes anteriores.
    """

    def __init__(self) -> None:
        self._heap: list[Patient] = []
        self._next_id = 1
        self._next_arrival_order = 0

    def enqueue(self, nombre: str, prioridad: int) -> Patient:
        """Crea e incorpora un paciente y devuelve la entidad creada."""

        patient = Patient(
            id=f"p-{self._next_id:04d}",
            nombre=nombre,
            prioridad=prioridad,
            orden_llegada=self._next_arrival_order,
        )
        self._next_id += 1
        self._next_arrival_order += 1
        heapq.heappush(self._heap, patient)
        return patient

    def list_ordered(self) -> list[Patient]:
        """Devuelve una copia ordenada sin mutar la cola."""

        return sorted(self._heap)

    def peek(self) -> Patient | None:
        """Devuelve el próximo paciente sin retirarlo."""

        return self._heap[0] if self._heap else None

    def attend_next(self) -> Patient | None:
        """Retira y devuelve el próximo paciente, o ``None`` si está vacía."""

        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def remove_by_id(self, patient_id: str) -> Patient | None:
        """Retira y devuelve el paciente con el ID indicado, si existe."""

        for index, patient in enumerate(self._heap):
            if patient.id == patient_id:
                removed = self._heap.pop(index)
                heapq.heapify(self._heap)
                return removed
        return None

    def remove_by_name(self, nombre: str) -> Patient | None:
        """Retira la primera coincidencia en el orden de atención."""

        patient = next(
            (candidate for candidate in self.list_ordered() if candidate.nombre == nombre),
            None,
        )
        if patient is None:
            return None
        return self.remove_by_id(patient.id)

    def __len__(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return not self._heap
