"""Página raíz que compone formulario y cola sin duplicar sus selectores."""

from playwright.sync_api import Page, expect

from .patient_form import PatientForm
from .patient_queue_view import PatientQueueView


class HospitalDashboardPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.form = PatientForm(page)
        self.queue = PatientQueueView(page)
        page.set_default_timeout(10_000)
        page.set_default_navigation_timeout(15_000)

    def open(self) -> None:
        response = self.page.goto(self.base_url + "/")
        assert response is not None and response.status == 200
        expect(self.page.get_by_role("heading", name="Atención de pacientes", exact=True)).to_be_visible()

    def reload(self) -> None:
        self.page.reload()

    def expect_flash(self, message: str, category: str = "success") -> None:
        flash = self.page.get_by_test_id("flash-message")
        expect(flash).to_contain_text(message)
        expect(flash).to_have_attribute("data-category", category)

    def use_viewport(self, width: int, height: int) -> None:
        self.page.set_viewport_size({"width": width, "height": height})

    def expect_usable_form(self) -> None:
        expect(self.form.name).to_be_visible()
        expect(self.form.priority).to_be_visible()
        expect(self.form.submit_button).to_be_visible()
        assert self.page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        ), "El dashboard no debe desbordarse horizontalmente."
