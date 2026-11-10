"""Instancia HTTP, contexto de navegador y cola aislada por recorrido."""

import json
import os
import threading
from pathlib import Path

import pytest

from pages.contracts import QueueActions, QueueReader
from pages.hospital_dashboard_page import HospitalDashboardPage
from support.queue_state import QueueState


@pytest.fixture(scope="session")
def hospital_url():
    external = os.environ.get("E2E_BASE_URL", "").rstrip("/")
    if external:
        if os.environ.get("E2E_ALLOW_CLEANUP") != "1":
            raise pytest.UsageError(
                "La URL E2E debe ser exclusiva de pruebas: confirma E2E_ALLOW_CLEANUP=1."
            )
        yield external
        return
    if os.environ.get("CI"):
        raise pytest.UsageError("CI requiere E2E_BASE_URL de la instancia desplegada.")

    # Sólo para desarrollo: servidor HTTP real en puerto asignado por el sistema.
    from app import create_app
    from werkzeug.serving import make_server

    server = make_server(
        "127.0.0.1", 0,
        create_app({"AMBIENTE": "e2e-local", "VERSION": "e2e-local"}),
        threaded=True,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.fixture(scope="session")
def queue_state(hospital_url):
    state = QueueState(hospital_url)
    health = state.health()
    assert health["estado"] == "ok"
    for variable, field in (("EXPECTED_AMBIENTE", "ambiente"), ("EXPECTED_VERSION", "version")):
        if os.environ.get(variable):
            assert health[field] == os.environ[variable], f"Health no coincide: {field}"
    report_dir = Path(os.environ.get("E2E_REPORT_DIR", "reports/e2e"))
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "target.json").write_text(
        json.dumps({"url": hospital_url, "health": health}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Instancia E2E: {hospital_url}; health={health}")
    return state


@pytest.fixture
def clean_queue(queue_state):
    # Se ejecuta también la limpieza final si un recorrido falla a la mitad.
    try:
        queue_state.clear()
        yield
    finally:
        queue_state.clear()


@pytest.fixture
def dashboard(page, hospital_url, clean_queue):
    dashboard_page = HospitalDashboardPage(page, hospital_url)
    dashboard_page.open()
    return dashboard_page


@pytest.fixture
def queue(dashboard) -> QueueReader:
    """Los tests de lectura sólo consumen QueueReader."""
    return dashboard.queue


@pytest.fixture
def queue_actions(dashboard) -> QueueActions:
    """Los tests que mutan la cola consumen la interfaz de acciones."""
    return dashboard.queue


@pytest.fixture
def patient_name(request):
    return "Paciente " + request.node.originalname.removeprefix("test_").replace("_", " ")
