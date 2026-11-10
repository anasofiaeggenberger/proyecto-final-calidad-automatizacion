"""Regresiones de eliminación de pacientes desde el dashboard HTML."""

import pytest

from app import create_app
from services.patient_service import PatientService


@pytest.fixture
def html_client_and_service():
    service = PatientService()
    flask_app = create_app(config={"TESTING": True}, service=service)

    with flask_app.test_client() as client:
        yield client, service


def test_html_deletes_second_homonym_by_id_without_deleting_first(
    html_client_and_service,
):
    client, service = html_client_and_service
    first = service.registrar("Ana", 3)
    second = service.registrar("Ana", 3)

    response = client.post(f"/eliminar/{second.id}")

    assert response.status_code == 302
    assert service.listar() == [first]


def test_html_deletes_patient_whose_name_contains_slash(html_client_and_service):
    client, service = html_client_and_service
    patient = service.registrar("A/B", 2)

    page = client.get("/")
    response = client.post(f"/eliminar/{patient.id}")

    assert page.status_code == 200
    assert f'action="/eliminar/{patient.id}"' in page.get_data(as_text=True)
    assert response.status_code == 302
    assert service.listar() == []


def test_html_reports_unknown_id_without_mutating_queue(html_client_and_service):
    client, service = html_client_and_service
    patient = service.registrar("Paciente", 2)

    response = client.post("/eliminar/p-9999", follow_redirects=True)

    assert response.status_code == 200
    assert "No se encontró un paciente con ID p-9999" in response.get_data(as_text=True)
    assert service.listar() == [patient]


def test_html_deletes_normal_patient_by_id(html_client_and_service):
    client, service = html_client_and_service
    patient = service.registrar("Paciente normal", 4)

    response = client.post(f"/eliminar/{patient.id}")

    assert response.status_code == 302
    assert service.listar() == []


def test_html_deletion_preserves_queue_order_and_fifo(
    html_client_and_service,
):
    client, service = html_client_and_service
    first = service.registrar("Primero", 2)
    urgent = service.registrar("Urgente", 1)
    second = service.registrar("Segundo", 2)

    response = client.post(f"/eliminar/{urgent.id}")

    assert response.status_code == 302
    assert service.listar() == [first, second]
    assert service.atender_siguiente() == first
    assert service.atender_siguiente() == second
    assert service.atender_siguiente() is None
