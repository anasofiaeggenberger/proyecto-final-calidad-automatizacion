"""E2E-13: equivalencias móvil/tablet y transición alta → atención."""

import pytest

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("width,height", [(390, 844), (768, 1024)], ids=["movil", "tablet"])
def test_dashboard_responsive_permite_completar_atencion(dashboard, queue, queue_actions, width, height):
    dashboard.use_viewport(width, height)
    dashboard.expect_usable_form()
    dashboard.form.register("Paciente responsive", 2)
    queue.expect_patients(["Paciente responsive"], [2])
    queue.expect_summary(1, 1, "Paciente responsive")
    queue_actions.attend_next()
    dashboard.expect_flash("Paciente responsive fue atendido correctamente.")
    queue.expect_empty()
