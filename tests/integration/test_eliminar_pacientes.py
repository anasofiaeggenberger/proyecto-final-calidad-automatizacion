"""I-24/I-29: eliminación por id, ids inexistentes y efecto sobre la cola."""


def test_eliminar_existente_responde_204_sin_cuerpo(api):
    paciente = api.registrar("Para eliminar", 3).json()["paciente"]

    respuesta = api.delete(f"/api/pacientes/{paciente['id']}")

    assert respuesta.status == 204
    assert respuesta.body == b""
    assert api.get("/api/pacientes").json()["total"] == 0


def test_eliminar_id_inexistente_responde_404(api):
    respuesta = api.delete("/api/pacientes/p-9999")

    assert respuesta.status == 404
    assert respuesta.codigo_error == "PACIENTE_NO_ENCONTRADO"


def test_eliminar_id_mal_formado_responde_404(api):
    respuesta = api.delete("/api/pacientes/no-es-un-id")

    assert respuesta.status == 404
    assert respuesta.codigo_error == "PACIENTE_NO_ENCONTRADO"


def test_eliminar_dos_veces_el_mismo_id_responde_404(api):
    paciente = api.registrar("Duplicada", 2).json()["paciente"]

    assert api.delete(f"/api/pacientes/{paciente['id']}").status == 204
    assert api.delete(f"/api/pacientes/{paciente['id']}").status == 404


def test_eliminar_inexistente_no_muta_la_cola(api):
    api.registrar("Intacta", 3)

    assert api.delete("/api/pacientes/p-4242").status == 404

    cuerpo = api.get("/api/pacientes").json()
    assert cuerpo["total"] == 1
    assert cuerpo["pacientes"][0]["nombre"] == "Intacta"


def test_eliminar_mantiene_el_orden_de_los_demas(api):
    api.registrar("Crítica", 1)
    media = api.registrar("Media", 3).json()["paciente"]
    api.registrar("Baja", 5)

    assert api.delete(f"/api/pacientes/{media['id']}").status == 204

    cuerpo = api.get("/api/pacientes").json()
    assert [p["nombre"] for p in cuerpo["pacientes"]] == ["Crítica", "Baja"]


def test_eliminar_por_id_distingue_homonimos(api):
    primero = api.registrar("Luis Pérez", 3).json()["paciente"]
    segundo = api.registrar("Luis Pérez", 3).json()["paciente"]

    assert api.delete(f"/api/pacientes/{segundo['id']}").status == 204

    cuerpo = api.get("/api/pacientes").json()
    assert cuerpo["total"] == 1
    assert cuerpo["pacientes"][0]["id"] == primero["id"]
