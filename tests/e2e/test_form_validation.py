"""E2E-07..12: equivalencias, valores límite y validación sin mutación."""

import pytest

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("priority", [1, 5], ids=["minima", "maxima"])
def test_limites_validos_de_urgencia(dashboard, queue, priority):
    dashboard.form.register("A", priority)
    queue.expect_patients(["A"], [priority])
    queue.expect_summary(1, int(priority <= 2), "A")


@pytest.mark.parametrize("priority", ["0", "6"], ids=["debajo", "encima"])
def test_servidor_rechaza_urgencia_fuera_de_rango(dashboard, queue, priority):
    dashboard.form.submit_tampered_priority("Paciente invalido", priority)
    dashboard.expect_flash("Selecciona un nivel de urgencia válido del 1 al 5.", "error")
    queue.expect_empty()


def test_nombre_vacio_es_obligatorio_en_el_navegador(dashboard, queue):
    dashboard.form.register("", 3)
    dashboard.form.expect_required_name()
    queue.expect_empty()


def test_nombre_de_espacios_es_rechazado_por_el_servidor(dashboard, queue):
    dashboard.form.register("   ", 3)
    dashboard.expect_flash("Ingresa el nombre del paciente.", "error")
    queue.expect_empty()


def test_prioridad_sin_seleccionar_es_obligatoria(dashboard, queue):
    dashboard.form.submit_without_priority("Paciente sin urgencia")
    dashboard.form.expect_required_priority()
    queue.expect_empty()


def test_nombre_se_normaliza_sin_perder_tildes(dashboard, queue):
    dashboard.form.register("  María López  ", 2)
    dashboard.expect_flash("María López fue registrado")
    queue.expect_patients(["María López"], [2])
    queue.expect_summary(1, 1, "María López")


def test_nombres_duplicados_conservan_ambos_registros(dashboard, queue, queue_actions):
    """Equivalencia y estado: dos personas pueden tener el mismo nombre."""
    dashboard.form.register("Nombre repetido", 3)
    dashboard.form.register("Nombre repetido", 3)
    queue.expect_patients(["Nombre repetido", "Nombre repetido"], [3, 3])
    queue_actions.attend_next()
    queue.expect_patients(["Nombre repetido"], [3])
    queue.expect_summary(1, 0, "Nombre repetido")
