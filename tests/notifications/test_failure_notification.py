"""Contrato del correo y TLS, sin enviar mensajes a destinatarios reales."""

import ssl
from unittest.mock import MagicMock

import pytest

from scripts.notificar_fallo import build_message, recipients, send_message


def message():
    return build_message(
        "build@example.test", "destino@example.test", build="42", commit="a" * 40,
        environment="staging", stage="E2E Tests", log_url="http://localhost:8080/job/hospital/42/console",
    )


def test_correo_incluye_los_datos_obligatorios():
    text = message().get_content()
    for value in ["42", "a" * 40, "staging", "E2E Tests", "/42/console"]:
        assert value in text
    assert message()["To"] == "destino@example.test"


@pytest.mark.parametrize("value", ["", "sin-correo", "correo@example.test\nBcc: otro@example.test"])
def test_rechaza_destinatarios_invalidos(value):
    with pytest.raises(ValueError):
        recipients(value)


def test_admite_varios_destinatarios():
    assert recipients("uno@example.test; dos@example.test") == ["uno@example.test", "dos@example.test"]


def test_starttls_ocurre_antes_del_login(monkeypatch):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.send_message.return_value = {}
    smtp = factory.return_value.__enter__.return_value
    monkeypatch.setattr("scripts.notificar_fallo.smtplib.SMTP", factory)
    send_message(message(), {"host": "smtp.example.test", "port": 587}, "usuario", "secreto-de-prueba")
    assert [call[0] for call in smtp.method_calls] == ["ehlo", "starttls", "ehlo", "login", "send_message"]
    assert isinstance(smtp.starttls.call_args.kwargs["context"], ssl.SSLContext)
    factory.assert_called_once_with("smtp.example.test", 587, timeout=15)


def test_ssl_no_degrada_a_conexion_sin_tls(monkeypatch):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.send_message.return_value = {}
    monkeypatch.setattr("scripts.notificar_fallo.smtplib.SMTP_SSL", factory)
    send_message(message(), {"host": "smtp.example.test", "port": 465, "tls": "ssl"}, "usuario", "secreto-de-prueba")
    smtp = factory.return_value.__enter__.return_value
    smtp.starttls.assert_not_called()
    smtp.login.assert_called_once()
    assert isinstance(factory.call_args.kwargs["context"], ssl.SSLContext)


@pytest.mark.parametrize("username,password", [("", "clave"), ("usuario", "")])
def test_no_abre_red_sin_credenciales(monkeypatch, username, password):
    factory = MagicMock()
    factory.return_value.__enter__.return_value.send_message.return_value = {}
    monkeypatch.setattr("scripts.notificar_fallo.smtplib.SMTP", factory)
    with pytest.raises(ValueError):
        send_message(message(), {"host": "smtp.example.test", "port": 587}, username, password)
    factory.assert_not_called()


def test_rechaza_modo_smtp_sin_tls():
    with pytest.raises(ValueError):
        send_message(message(), {"host": "smtp.example.test", "port": 25, "tls": "none"}, "usuario", "clave")

def test_rechazo_parcial_no_se_informa_como_exito(monkeypatch):
    import smtplib
    factory = MagicMock()
    factory.return_value.__enter__.return_value.send_message.return_value = {
        "otro@example.test": (550, b"rejected")
    }
    monkeypatch.setattr("scripts.notificar_fallo.smtplib.SMTP", factory)
    email = message()
    email.replace_header("To", "destino@example.test, otro@example.test")
    with pytest.raises(smtplib.SMTPRecipientsRefused):
        send_message(email, {"host": "smtp.example.test", "port": 587}, "usuario", "clave")
