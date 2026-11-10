"""I-13/I-18: listado, próximo paciente, orden por urgencia y FIFO."""


def test_listado_vacio_responde_200(api):
    respuesta = api.get("/api/pacientes")

    assert respuesta.status == 200
    cuerpo = respuesta.json()
    assert cuerpo == {"total": 0, "proximo": None, "pacientes": []}


def test_listado_con_un_paciente_lo_marca_como_proximo(api):
    creado = api.registrar("Única", 4).json()["paciente"]

    cuerpo = api.get("/api/pacientes").json()

    assert cuerpo["total"] == 1
    assert cuerpo["proximo"] == creado
    assert cuerpo["pacientes"] == [creado]


def test_listado_ordena_por_urgencia(api):
    for nombre, prioridad in [("Media", 3), ("Crítica", 1), ("Baja", 5), ("Alta", 2)]:
        api.registrar(nombre, prioridad)

    cuerpo = api.get("/api/pacientes").json()

    assert [p["nombre"] for p in cuerpo["pacientes"]] == [
        "Crítica",
        "Alta",
        "Media",
        "Baja",
    ]
    assert cuerpo["proximo"]["nombre"] == "Crítica"


def test_listado_respeta_fifo_en_empate_de_urgencia(api):
    for nombre in ["Primero", "Segundo", "Tercero"]:
        api.registrar(nombre, 2)

    cuerpo = api.get("/api/pacientes").json()

    assert [p["nombre"] for p in cuerpo["pacientes"]] == [
        "Primero",
        "Segundo",
        "Tercero",
    ]
    # el orden de llegada no se reinicia entre pruebas: sólo debe ser creciente
    ordenes = [p["orden_llegada"] for p in cuerpo["pacientes"]]
    assert ordenes == sorted(ordenes)
    assert len(set(ordenes)) == 3


def test_listado_no_modifica_la_cola(api):
    api.registrar("Permanente", 3)

    primero = api.get("/api/pacientes").json()
    segundo = api.get("/api/pacientes").json()

    assert primero == segundo
    assert segundo["total"] == 1
