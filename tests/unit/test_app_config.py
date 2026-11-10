"""Configuración segura por instancia sin cambiar el contrato de Flask."""

from app import create_app


def test_clave_de_desarrollo_es_aleatoria_por_instancia(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    first, second = create_app(), create_app()
    assert len(first.secret_key) >= 32 and first.secret_key != second.secret_key


def test_clave_explicita_se_respeta(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "configuracion-de-prueba")
    assert create_app().secret_key == "configuracion-de-prueba"
    assert create_app({"SECRET_KEY": "config-local"}).secret_key == "config-local"
