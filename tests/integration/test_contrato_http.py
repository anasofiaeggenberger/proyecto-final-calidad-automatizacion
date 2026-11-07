"""I-30/I-35: contrato HTTP, métodos permitidos, esquema y aislamiento."""

import pytest

CLAVES_PACIENTE = {"id", "nombre", "prioridad", "orden_llegada"}
CLAVES_ERROR = {"codigo", "mensaje", "detalles"}


@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [
        ("GET", "/api/pacientes/atender"),
        ("PUT", "/api/pacientes"),
        ("PATCH", "/api/pacientes"),
        ("DELETE", "/api/pacientes"),
        ("POST", "/api/health"),
    ],
)
def test_metodos_no_permitidos_responden_405_en_json(api, metodo, ruta):
    respuesta = api.request(metodo, ruta)

    assert respuesta.status == 405
    assert "application/json" in respuesta.content_type
    assert respuesta.codigo_error == "METODO_NO_PERMITIDO"


def test_ruta_api_inexistente_responde_404_en_json(api):
    respuesta = api.get("/api/pacientes/p-0001/historial")

    assert respuesta.status == 404
    assert "application/json" in respuesta.content_type
    assert respuesta.codigo_error == "RECURSO_NO_ENCONTRADO"


def test_el_dashboard_html_sigue_disponible(api):
    respuesta = api.get("/")

    assert respuesta.status == 200
    assert "text/html" in respuesta.content_type


def test_el_esquema_del_paciente_no_expone_campos_extra(api):
    api.registrar("Esquema", 2)

    for paciente in api.get("/api/pacientes").json()["pacientes"]:
        assert set(paciente) == CLAVES_PACIENTE
        assert isinstance(paciente["id"], str)
        assert isinstance(paciente["prioridad"], int)
        assert isinstance(paciente["orden_llegada"], int)


def test_el_esquema_de_error_es_uniforme(api):
    error = api.registrar("Error", 7).json()["error"]

    assert set(error) == CLAVES_ERROR
    assert isinstance(error["codigo"], str) and error["codigo"]
    assert isinstance(error["mensaje"], str) and error["mensaje"]
    assert isinstance(error["detalles"], dict)


def test_las_respuestas_json_declaran_su_content_type(api):
    for ruta in ["/api/health", "/api/pacientes"]:
        assert "application/json" in api.get(ruta).content_type


def test_la_cola_llega_vacia_a_cada_prueba(api):
    assert api.get("/api/pacientes").json()["total"] == 0
    api.registrar("Residuo", 3)
    assert api.get("/api/pacientes").json()["total"] == 1


def test_la_cola_llega_vacia_a_cada_prueba_tambien_despues(api):
    assert api.get("/api/pacientes").json()["total"] == 0
