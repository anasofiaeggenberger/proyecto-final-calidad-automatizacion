"""Fixtures de integración: instancia bajo prueba y aislamiento de datos."""

import os
import socket
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

import pytest

from api_client import ApiClient

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
AMBIENTE_LOCAL = "local"
VERSION_LOCAL = "integracion-local"
ESPERA_ARRANQUE = 30.0


def _puerto_libre() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _esperar_health(cliente: ApiClient, limite: float) -> bool:
    fin = time.monotonic() + limite
    while time.monotonic() < fin:
        try:
            if cliente.get("/api/health").status == 200:
                return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.2)
    return False


@pytest.fixture(scope="session")
def api_base_url():
    """URL de la API desplegada; si no hay una, levanta una instancia propia."""

    url_externa = os.environ.get("API_BASE_URL")
    if url_externa:
        cliente = ApiClient(url_externa.rstrip("/"))
        if not _esperar_health(cliente, ESPERA_ARRANQUE):
            pytest.fail(f"la API de {url_externa} no respondió /api/health")
        yield url_externa.rstrip("/")
        return

    puerto = _puerto_libre()
    entorno = {
        **os.environ,
        "APP_AMBIENTE": AMBIENTE_LOCAL,
        "APP_VERSION": VERSION_LOCAL,
    }
    proceso = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from app import create_app; "
            f"create_app().run(host='127.0.0.1', port={puerto})",
        ],
        cwd=RAIZ_PROYECTO,
        env=entorno,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{puerto}"
    try:
        if not _esperar_health(ApiClient(url), ESPERA_ARRANQUE):
            pytest.fail("la instancia local de la API no arrancó")
        yield url
    finally:
        # la cola vive en memoria: el proceso se apaga siempre para no filtrar estado
        proceso.terminate()
        try:
            proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=5)


@pytest.fixture(scope="session")
def ambiente_esperado(api_base_url) -> str:
    return os.environ.get("EXPECTED_AMBIENTE") or (
        AMBIENTE_LOCAL if not os.environ.get("API_BASE_URL") else ""
    )


@pytest.fixture(scope="session")
def version_esperada(api_base_url) -> str:
    return os.environ.get("EXPECTED_VERSION") or (
        VERSION_LOCAL if not os.environ.get("API_BASE_URL") else ""
    )


def _vaciar_cola(cliente: ApiClient) -> None:
    for paciente in cliente.get("/api/pacientes").json()["pacientes"]:
        cliente.delete(f"/api/pacientes/{paciente['id']}")


@pytest.fixture
def api(api_base_url):
    """Entrega un cliente sobre una cola vacía y la deja vacía al terminar."""

    cliente = ApiClient(api_base_url)
    _vaciar_cola(cliente)
    assert cliente.get("/api/pacientes").json()["total"] == 0
    yield cliente
    _vaciar_cola(cliente)
