"""Cliente HTTP mínimo para probar la API como caja negra."""

import json
import urllib.error
import urllib.request


class Respuesta:
    """Resultado de una petición HTTP real contra la API."""

    def __init__(self, status: int, headers: dict, body: bytes):
        self.status = status
        self.headers = headers
        self.body = body

    @property
    def content_type(self) -> str:
        return self.headers.get("Content-Type", "")

    def json(self):
        return json.loads(self.body.decode("utf-8"))

    @property
    def codigo_error(self) -> str | None:
        try:
            return self.json()["error"]["codigo"]
        except (ValueError, KeyError, TypeError):
            return None


class ApiClient:
    """Envía peticiones HTTP sin acoplarse al cliente de pruebas de Flask."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        json_body=None,
        raw_body: str | None = None,
        content_type: str | None = "application/json",
    ) -> Respuesta:
        data = None
        if raw_body is not None:
            data = raw_body.encode("utf-8")
        elif json_body is not None:
            data = json.dumps(json_body).encode("utf-8")

        headers = {"Accept": "application/json"}
        if data is not None and content_type is not None:
            headers["Content-Type"] = content_type

        peticion = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout) as respuesta:
                return Respuesta(
                    respuesta.status, dict(respuesta.headers), respuesta.read()
                )
        except urllib.error.HTTPError as error:
            # los códigos 4xx son resultados esperados del contrato, no fallos
            return Respuesta(error.code, dict(error.headers), error.read())

    def get(self, path: str) -> Respuesta:
        return self.request("GET", path)

    def post(self, path: str, json_body=None, **kwargs) -> Respuesta:
        return self.request("POST", path, json_body=json_body, **kwargs)

    def delete(self, path: str) -> Respuesta:
        return self.request("DELETE", path)

    def registrar(self, nombre: str, prioridad: int) -> Respuesta:
        return self.post("/api/pacientes", {"nombre": nombre, "prioridad": prioridad})
