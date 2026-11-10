"""E2E-02/03: prioridad y FIFO; decisión y transiciones de atención."""

import pytest

pytestmark = pytest.mark.e2e


def test_menor_prioridad_y_empates_fifo(dashboard, queue, queue_actions):
    for name, priority in [("Estable", 3), ("Urgente primero", 1), ("Urgente segundo", 1)]:
        dashboard.form.register(name, priority)
    queue.expect_patients(["Urgente primero", "Urgente segundo", "Estable"], [1, 1, 3])
    queue.expect_summary(3, 2, "Urgente primero")

    queue_actions.attend_next()
    dashboard.expect_flash("Urgente primero fue atendido correctamente.")
    queue.expect_patients(["Urgente segundo", "Estable"], [1, 3])
    queue.expect_summary(2, 1, "Urgente segundo")
    queue_actions.attend_next()
    dashboard.expect_flash("Urgente segundo fue atendido correctamente.")
    queue.expect_summary(1, 0, "Estable")
    queue_actions.attend_next()
    dashboard.expect_flash("Estable fue atendido correctamente.")
    queue.expect_empty()
    queue_actions.attend_next()
    dashboard.expect_flash("La cola está vacía. No hay pacientes por atender.", "info")
    queue.expect_empty()


def test_todos_los_niveles_se_ordenan_por_urgencia(dashboard, queue, queue_actions):
    """Particiones de equivalencia: todos los niveles válidos, alta desordenada."""
    for priority in [5, 3, 1, 4, 2]:
        dashboard.form.register(f"Nivel {priority}", priority)
    queue.expect_patients([f"Nivel {p}" for p in range(1, 6)], list(range(1, 6)))
    queue.expect_summary(5, 2, "Nivel 1")
    for priority in range(1, 6):
        queue_actions.attend_next()
        dashboard.expect_flash(f"Nivel {priority} fue atendido correctamente.")
    queue.expect_empty()
