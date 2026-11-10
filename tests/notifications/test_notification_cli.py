"""Flujo CLI y status.json sin conexiones a buzones reales."""

import json
import os
import smtplib
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts import notificar_fallo

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def cli(monkeypatch, tmp_path):
    config = tmp_path / "smtp.json"
    config.write_text(json.dumps({"host": "smtp.example.test", "port": 587, "sender": "build@example.test"}))
    report = tmp_path / "reports" / "notifications" / "status.json"
    monkeypatch.setenv("SMTP_CONFIG_FILE", str(config))
    monkeypatch.setenv("SMTP_USERNAME", "usuario")
    monkeypatch.setenv("SMTP_PASSWORD", "audit-secret")
    args = ["--to", "destino@example.test", "--build", "42", "--commit", "a" * 40,
            "--environment", "ci", "--stage", "E2E Tests", "--log-url", "http://localhost/42/console",
            "--report", str(report)]
    monkeypatch.setattr(sys, "argv", ["notificar_fallo.py", *args])
    return config, report, args


def test_cli_exitoso_guarda_metadatos_y_estado(cli, monkeypatch):
    _, report, _ = cli
    sender = MagicMock()
    monkeypatch.setattr(notificar_fallo, "send_message", sender)
    assert notificar_fallo.main() == 0
    status = json.loads(report.read_text())
    assert status["status"] == "accepted_by_smtp"
    assert status["commit"] == "a" * 40 and status["stage"] == "E2E Tests"
    assert "audit-secret" not in report.read_text()
    sender.assert_called_once()


@pytest.mark.parametrize("content", ["null", "[]", "{invalido", '{"host":"smtp.example.test","port":null,"sender":"build@example.test"}'])
def test_cli_configuracion_invalida_falla_sin_abrir_red(cli, monkeypatch, content):
    config, report, _ = cli
    config.write_text(content)
    network = MagicMock()
    monkeypatch.setattr(notificar_fallo.smtplib, "SMTP", network)
    assert notificar_fallo.main() == 1
    assert json.loads(report.read_text())["status"] == "failed"
    network.assert_not_called()


@pytest.mark.parametrize("variable", ["SMTP_USERNAME", "SMTP_PASSWORD"])
def test_cli_sin_credenciales_falla_y_crea_reporte(cli, monkeypatch, variable):
    _, report, _ = cli
    monkeypatch.delenv(variable)
    network = MagicMock()
    monkeypatch.setattr(notificar_fallo.smtplib, "SMTP", network)
    assert notificar_fallo.main() == 1
    assert json.loads(report.read_text())["status"] == "failed"
    network.assert_not_called()


@pytest.mark.parametrize("failure", [
    smtplib.SMTPAuthenticationError(535, b"audit-secret"),
    smtplib.SMTPServerDisconnected("audit-secret"),
    smtplib.SMTPRecipientsRefused({"destino@example.test": (550, b"audit-secret")}),
])
def test_cli_error_smtp_no_expone_secretos(cli, monkeypatch, capsys, failure):
    _, report, _ = cli
    monkeypatch.setattr(notificar_fallo, "send_message", MagicMock(side_effect=failure))
    assert notificar_fallo.main() == 1
    status = json.loads(report.read_text())
    assert status["status"] == "failed"
    assert status["error_type"] == type(failure).__name__
    assert "audit-secret" not in capsys.readouterr().out + report.read_text()


def test_cli_real_sin_configuracion_devuelve_uno(cli):
    _, report, args = cli
    env = {k: v for k, v in os.environ.items() if not k.startswith("SMTP_")}
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/notificar_fallo.py"), *args],
        env=env, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert json.loads(report.read_text())["error_type"] == "KeyError"
    assert "Traceback" not in result.stderr
