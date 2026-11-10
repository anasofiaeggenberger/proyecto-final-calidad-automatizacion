"""Lectura y acciones de la tabla, resumen y estado vacío."""

from playwright.sync_api import Page, expect


class PatientQueueView:
    """Implementa estructuralmente QueueReader y QueueActions."""

    def __init__(self, page: Page):
        self.page = page
        self.rows = page.get_by_test_id("patient-row")

    def expect_patients(self, names: list[str], priorities: list[int] | None = None) -> None:
        expect(self.rows).to_have_count(len(names))
        for index, name in enumerate(names):
            row = self.rows.nth(index)
            expect(row).to_have_attribute("data-patient-name", name)
            expect(row.get_by_role("cell").nth(1)).to_contain_text(name)
            if priorities is not None:
                expect(row).to_have_attribute("data-priority", str(priorities[index]))

    def expect_summary(self, total: int, urgent: int, next_patient: str | None) -> None:
        # Cada tarjeta contiene etiqueta, valor y detalle en párrafos semánticos.
        expect(self.page.get_by_test_id("summary-total").locator("p").nth(1)).to_have_text(str(total))
        expect(self.page.get_by_test_id("summary-urgent").locator("p").nth(1)).to_have_text(str(urgent))
        if next_patient is None:
            expect(self.page.get_by_test_id("next-patient-name")).to_have_count(0)
            expect(self.page.get_by_test_id("summary-next")).to_contain_text("No hay pacientes pendientes")
        else:
            expect(self.page.get_by_test_id("next-patient-name")).to_have_text(next_patient)

    def expect_empty(self) -> None:
        expect(self.page.get_by_test_id("empty-state")).to_be_visible()
        expect(self.rows).to_have_count(0)
        expect(self.page.get_by_test_id("patient-table")).to_have_count(0)
        self.expect_summary(0, 0, None)

    def attend_next(self) -> None:
        self.page.get_by_test_id("attend-next-button").click()

    def delete(self, name: str, *, confirm: bool = True) -> None:
        row = self.rows.filter(has=self.page.get_by_text(name, exact=True))
        expect(row).to_have_count(1)
        self.page.once("dialog", lambda dialog: dialog.accept() if confirm else dialog.dismiss())
        row.get_by_test_id("delete-patient-button").click()
