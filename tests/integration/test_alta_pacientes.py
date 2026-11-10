"""I-03/I-12: alta de pacientes, particiones de equivalencia y valores límite."""

import pytest

CLAVES_PACIENTE = {"id", "nombre", "prioridad", "orden_llegada"}


@pytest.mark.smoke
def test_alta_valida_devuelve_201_con_paciente_y_posicion(api):
    respuesta = api.registrar("Ana López", 2)

    assert respuesta.status == 201
    cuerpo = respuesta.json()
    assert set(cuerpo["paciente"]) == CLAVES_PACIENTE
    assert cuerpo["paciente"]["nombre"] == "Ana López"
    assert cuerpo["paciente"]["prioridad"] == 2
    assert cuerpo["posicion"] == 1


@pytest.mark.parametrize("prioridad", [1, 2, 3, 4, 5])
def test_alta_acepta_todas_las_prioridades_del_rango(api, prioridad):
    assert api.registrar(f"Paciente {prioridad}", prioridad).status == 201


@pytest.mark.parametrize("prioridad", [0, -1, 6, 99])
def test_alta_rechaza_prioridades_fuera_del_rango(api, prioridad):
    respuesta = api.registrar("Fuera de rango", prioridad)

    assert respuesta.status == 400
    assert respuesta.codigo_error == "PRIORIDAD_INVALIDA"


@pytest.mark.parametrize("prioridad", ["2", "", 2.5, None, True, [2], {"valor": 2}])
def test_alta_rechaza_prioridades_con_tipo_invalido(api, prioridad):
    respuesta = api.registrar("Tipo inválido", prioridad)

    assert respuesta.status == 400
    assert respuesta.codigo_error == "PRIORIDAD_INVALIDA"


def test_alta_rechaza_prioridad_ausente(api):
    respuesta = api.post("/api/pacientes", {"nombre": "Sin prioridad"})

    assert respuesta.status == 400
    assert respuesta.codigo_error == "PRIORIDAD_INVALIDA"


@pytest.mark.parametrize("nombre", ["", "   ", "\t\n", None, 123, [], {}])
def test_alta_rechaza_nombres_invalidos(api, nombre):
    respuesta = api.registrar(nombre, 3)

    assert respuesta.status == 400
    assert respuesta.codigo_error == "NOMBRE_INVALIDO"


def test_alta_rechaza_nombre_ausente(api):
    respuesta = api.post("/api/pacientes", {"prioridad": 3})

    assert respuesta.status == 400
    assert respuesta.codigo_error == "NOMBRE_INVALIDO"


def test_alta_acepta_el_nombre_mas_corto(api):
    respuesta = api.registrar("A", 3)

    assert respuesta.status == 201
    assert respuesta.json()["paciente"]["nombre"] == "A"


def test_alta_normaliza_espacios_del_nombre(api):
    respuesta = api.registrar("  Mario Díaz  ", 4)

    assert respuesta.status == 201
    assert respuesta.json()["paciente"]["nombre"] == "Mario Díaz"


def test_alta_invalida_no_muta_la_cola(api):
    api.registrar("Paciente válido", 3)

    assert api.registrar("Inválido", 9).status == 400

    cuerpo = api.get("/api/pacientes").json()
    assert cuerpo["total"] == 1
    assert cuerpo["pacientes"][0]["nombre"] == "Paciente válido"


def test_alta_rechaza_campos_desconocidos(api):
    respuesta = api.post(
        "/api/pacientes",
        {"nombre": "Extra", "prioridad": 2, "edad": 40},
    )

    assert respuesta.status == 400
    assert respuesta.codigo_error == "CAMPOS_DESCONOCIDOS"
    assert respuesta.json()["error"]["detalles"]["campos"] == ["edad"]


def test_alta_rechaza_cuerpo_ausente(api):
    respuesta = api.post("/api/pacientes")

    assert respuesta.status == 400
    assert respuesta.codigo_error == "JSON_INVALIDO"


@pytest.mark.parametrize("cuerpo", ["{", "[]", '"texto"', "null"])
def test_alta_rechaza_json_no_valido(api, cuerpo):
    respuesta = api.post("/api/pacientes", raw_body=cuerpo)

    assert respuesta.status == 400
    assert respuesta.codigo_error == "JSON_INVALIDO"


def test_alta_rechaza_content_type_incorrecto(api):
    respuesta = api.post(
        "/api/pacientes",
        raw_body='{"nombre": "Ana", "prioridad": 2}',
        content_type="text/plain",
    )

    assert respuesta.status == 400
    assert respuesta.codigo_error == "JSON_INVALIDO"


def test_alta_asigna_ids_distintos_a_homonimos(api):
    primero = api.registrar("Luis Pérez", 3).json()["paciente"]
    segundo = api.registrar("Luis Pérez", 3).json()["paciente"]

    assert primero["id"] != segundo["id"]
    assert primero["orden_llegada"] < segundo["orden_llegada"]


def test_alta_devuelve_la_posicion_segun_la_urgencia(api):
    api.registrar("Baja urgencia", 5)
    respuesta = api.registrar("Crítico", 1)

    assert respuesta.json()["posicion"] == 1
