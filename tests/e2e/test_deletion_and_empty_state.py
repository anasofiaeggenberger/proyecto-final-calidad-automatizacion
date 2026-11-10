"""E2E-04/05/06: eliminación; tabla de decisión y transición a cola vacía."""

import pytest

pytestmark = pytest.mark.e2e


def test_eliminar_reordena_hasta_cola_vacia(dashboard, queue, queue_actions):
    for name, priority in [("Intermedio", 3), ("Primero", 1), ("Ultimo", 5)]:
        dashboard.form.register(name, priority)
    queue_actions.delete("Intermedio")
    dashboard.expect_flash("Intermedio fue eliminado de la cola.")
    queue.expect_patients(["Primero", "Ultimo"], [1, 5])
    queue.expect_summary(2, 1, "Primero")
    queue_actions.delete("Primero")
    queue.expect_summary(1, 0, "Ultimo")
    queue_actions.delete("Ultimo")
    dashboard.expect_flash("Ultimo fue eliminado de la cola.")
    queue.expect_empty()


def test_cancelar_eliminacion_conserva_la_cola(dashboard, queue, queue_actions):
    """Decisión: confirmación=no no debe retirar el paciente."""
    dashboard.form.register("Paciente conservado", 2)
    queue_actions.delete("Paciente conservado", confirm=False)
    queue.expect_patients(["Paciente conservado"], [2])
    queue.expect_summary(1, 1, "Paciente conservado")
    dashboard.reload()
    queue.expect_patients(["Paciente conservado"], [2])


def test_atender_una_cola_inicialmente_vacia(dashboard, queue, queue_actions):
    queue.expect_empty()
    queue_actions.attend_next()
    dashboard.expect_flash("La cola está vacía. No hay pacientes por atender.", "info")
    queue.expect_empty()
