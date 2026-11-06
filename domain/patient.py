"""Entidad de dominio para un paciente en espera."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Patient:
    """Representa un paciente con prioridad y orden de llegada."""

    id: str
    nombre: str
    prioridad: int
    orden_llegada: int

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id debe ser una cadena no vacía")

        if not isinstance(self.nombre, str):
            raise TypeError("nombre debe ser una cadena")

        if isinstance(self.prioridad, bool) or not isinstance(self.prioridad, int):
            raise ValueError("prioridad debe ser un entero entre 1 y 5")
        if not 1 <= self.prioridad <= 5:
            raise ValueError("prioridad debe ser un entero entre 1 y 5")

        if (
            isinstance(self.orden_llegada, bool)
            or not isinstance(self.orden_llegada, int)
            or self.orden_llegada < 0
        ):
            raise ValueError("orden_llegada debe ser un entero no negativo")

    @property
    def sort_key(self) -> tuple[int, int]:
        """Clave de atención: mayor urgencia primero y FIFO en empate."""

        return self.prioridad, self.orden_llegada

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Patient):
            return NotImplemented
        return self.sort_key < other.sort_key
