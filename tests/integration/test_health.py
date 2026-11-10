"""I-01/I-02: salud de la instancia, ambiente y versión del artefacto."""

import pytest

CLAVES_HEALTH = {"estado", "ambiente", "version"}


@pytest.mark.smoke
def test_health_responde_ok_con_ambiente_y_version(api):
    respuesta = api.get("/api/health")

    assert respuesta.status == 200
    cuerpo = respuesta.json()
    assert CLAVES_HEALTH <= set(cuerpo)
    assert cuerpo["estado"] == "ok"
    assert cuerpo["ambiente"]
    assert cuerpo["version"]


def test_health_declara_json(api):
    assert "application/json" in api.get("/api/health").content_type


def test_health_expone_el_ambiente_desplegado(api, ambiente_esperado):
    if not ambiente_esperado:
        pytest.skip("no se declaró EXPECTED_AMBIENTE para esta instancia")

    assert api.get("/api/health").json()["ambiente"] == ambiente_esperado


def test_health_expone_la_version_del_artefacto(api, version_esperada):
    if not version_esperada:
        pytest.skip("no se declaró EXPECTED_VERSION para esta instancia")

    assert api.get("/api/health").json()["version"] == version_esperada
