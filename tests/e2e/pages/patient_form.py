"""Interacciones del formulario; los tests no conocen selectores."""

from playwright.sync_api import Page, expect


class PatientForm:
    def __init__(self, page: Page):
        self.page = page
        self.form = page.get_by_test_id("register-form")
        self.name = page.get_by_test_id("patient-name-input")
        self.priority = page.get_by_test_id("priority-select")
        self.submit_button = page.get_by_test_id("register-patient-button")

    def register(self, name: str, priority: int | str) -> None:
        self.name.fill(name)
        self.priority.select_option(str(priority))
        self.submit_button.click()

    def submit_without_priority(self, name: str) -> None:
        self.name.fill(name)
        self.submit_button.click()

    def expect_required_name(self) -> None:
        expect(self.name).to_be_focused()
        assert self.name.evaluate("(input) => input.validity.valueMissing")

    def expect_required_priority(self) -> None:
        expect(self.priority).to_be_focused()
        assert self.priority.evaluate("(input) => input.validity.valueMissing")

    def submit_tampered_priority(self, name: str, priority: str) -> None:
        """Envía un select manipulado para probar validación del servidor por UI."""
        self.name.fill(name)
        self.priority.evaluate(
            "(select, value) => select.add(new Option(value, value))", priority
        )
        self.priority.select_option(priority)
        self.submit_button.click()
