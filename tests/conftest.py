import pytest

from domain.patient_queue import PatientQueue
from services.patient_service import PatientService


@pytest.fixture
def patient_queue() -> PatientQueue:
    """Entrega una cola nueva para cada prueba que la solicite."""

    return PatientQueue()


@pytest.fixture
def patient_service() -> PatientService:
    """Entrega un servicio nuevo y aislado para cada prueba."""

    return PatientService()
