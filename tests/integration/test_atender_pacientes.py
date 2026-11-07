"""I-19/I-23: atención por urgencia, FIFO y comportamiento con cola vacía."""

import pytest

MENSAJE_COLA_VACIA = "La cola está vacía. No hay pacientes por atender."


@pytest.mark.smoke
def test_atender_entrega_al_paciente_mas_urgente(api):
    api.registrar("Baja", 5)
    api.registrar("Crítica", 1)

    respuesta = api.post("/api/pacientes/atender")

    assert respuesta.status == 200
    assert respuesta.json()["paciente"]["nombre"] == "Crítica"
    assert api.get("/api/pacientes").json()["total"] == 1


def test_atender_respeta_fifo_en_empate(api):
    api.registrar("Primero", 3)
    api.registrar("Segundo", 3)

    assert api.post("/api/pacientes/atender").json()["paciente"]["nombre"] == "Primero"
    assert api.post("/api/pacientes/atender").json()["paciente"]["nombre"] == "Segundo"


def test_atender_agota_la_cola_en_el_orden_esperado(api):
    for nombre, prioridad in [("C", 3), ("A", 1), ("B", 2)]:
        api.registrar(nombre, prioridad)

    atendidos = [
        api.post("/api/pacientes/atender").json()["paciente"]["nombre"]
        for _ in range(3)
    ]

    assert atendidos == ["A", "B", "C"]
    assert api.get("/api/pacientes").json()["total"] == 0


def test_atender_cola_vacia_responde_200_sin_paciente(api):
    respuesta = api.post("/api/pacientes/atender")

    assert respuesta.status == 200
    assert respuesta.json() == {"paciente": None, "mensaje": MENSAJE_COLA_VACIA}


def test_atender_cola_vacia_es_repetible_y_no_muta(api):
    for _ in range(3):
        assert api.post("/api/pacientes/atender").json()["paciente"] is None

    assert api.get("/api/pacientes").json()["total"] == 0
