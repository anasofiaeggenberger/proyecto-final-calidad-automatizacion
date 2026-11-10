"""E2E-01: alta y listado; partición válida y transición vacío → registrado."""

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.smoke]


def test_registro_y_listado_persisten_al_recargar(dashboard, queue, patient_name):
    queue.expect_empty()
    dashboard.form.register(patient_name, 3)
    dashboard.expect_flash(f"{patient_name} fue registrado con urgencia 3")
    queue.expect_patients([patient_name], [3])
    queue.expect_summary(1, 0, patient_name)
    dashboard.reload()
    queue.expect_patients([patient_name], [3])
    queue.expect_summary(1, 0, patient_name)
