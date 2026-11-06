"""Casos de uso de pacientes sin dependencias de Flask."""

from domain.patient import Patient
from domain.patient_queue import PatientQueue


class PatientServiceError(ValueError):
    """Error base para entradas inválidas del servicio."""


class InvalidPatientNameError(PatientServiceError):
    """Se produce cuando el nombre no es válido para registrar o buscar."""


class InvalidPriorityError(PatientServiceError):
    """Se produce cuando la prioridad no es un entero entre 1 y 5."""


class PatientService:
    """Coordina los casos de uso sobre una cola de pacientes aislada."""

    def __init__(self, queue: PatientQueue | None = None) -> None:
        self._queue = queue if queue is not None else PatientQueue()

    def registrar(self, nombre: str, prioridad: int | str) -> Patient:
        """Normaliza, valida y registra un paciente."""

        normalized_name = self._normalize_name(nombre)
        normalized_priority = self._normalize_priority(prioridad)
        return self._queue.enqueue(normalized_name, normalized_priority)

    def listar(self) -> list[Patient]:
        """Devuelve los pacientes en orden de atención."""

        return self._queue.list_ordered()

    def atender_siguiente(self) -> Patient | None:
        """Atiende y devuelve el siguiente paciente, si existe."""

        return self._queue.attend_next()

    def eliminar_por_id(self, patient_id: str) -> Patient | None:
        """Elimina y devuelve un paciente identificado por su ID."""

        return self._queue.remove_by_id(patient_id)

    def eliminar_por_nombre(self, nombre: str) -> Patient | None:
        """Elimina la primera coincidencia en orden de atención."""

        normalized_name = self._normalize_name(nombre)
        return self._queue.remove_by_name(normalized_name)

    def proximo(self) -> Patient | None:
        """Devuelve el siguiente paciente sin retirarlo."""

        return self._queue.peek()

    @staticmethod
    def _normalize_name(nombre: str) -> str:
        if not isinstance(nombre, str):
            raise InvalidPatientNameError("nombre debe ser una cadena no vacía")

        normalized_name = nombre.strip()
        if not normalized_name:
            raise InvalidPatientNameError("nombre debe ser una cadena no vacía")
        return normalized_name

    @staticmethod
    def _normalize_priority(prioridad: int | str) -> int:
        if isinstance(prioridad, bool):
            raise InvalidPriorityError("prioridad debe ser un entero entre 1 y 5")

        if isinstance(prioridad, int):
            normalized_priority = prioridad
        elif isinstance(prioridad, str):
            value = prioridad.strip()
            if not value or not value.isdecimal():
                raise InvalidPriorityError(
                    "prioridad debe ser un entero entre 1 y 5"
                )
            normalized_priority = int(value)
        else:
            raise InvalidPriorityError("prioridad debe ser un entero entre 1 y 5")

        if not 1 <= normalized_priority <= 5:
            raise InvalidPriorityError("prioridad debe ser un entero entre 1 y 5")
        return normalized_priority
