"""Limpieza HTTP de una instancia exclusiva de pruebas."""

import json
from urllib.request import Request, urlopen


class QueueState:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _request(self, path: str, method: str = "GET"):
        with urlopen(Request(self.base_url + path, method=method), timeout=10) as response:
            body = response.read()
            return json.loads(body) if body else None

    def health(self) -> dict:
        return self._request("/api/health")

    def clear(self) -> None:
        for patient in self._request("/api/pacientes")["pacientes"]:
            self._request("/api/pacientes/" + patient["id"], "DELETE")
        assert self._request("/api/pacientes")["total"] == 0, "No se pudo limpiar la cola."
