"""Envía el fallo real del build por SMTP con TLS y credenciales inyectadas."""

import argparse
import json
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import getaddresses
from pathlib import Path


def recipients(value: str) -> list[str]:
    if "\r" in value or "\n" in value:
        raise ValueError("Destinatarios inválidos")
    parsed = getaddresses([value.replace(";", ",")])
    addresses = [address for _, address in parsed]
    if not addresses or any(not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", a) for a in addresses):
        raise ValueError("Destinatarios inválidos")
    return addresses


def build_message(sender: str, to: str, *, build: str, commit: str, environment: str,
                  stage: str, log_url: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients(to))
    message["Subject"] = f"Fallo hospital - build {build} - {environment}"
    message.set_content(
        f"Build: {build}\nCommit: {commit}\nAmbiente: {environment}\n"
        f"Etapa fallida: {stage}\nLog: {log_url}\n"
        "Las etapas posteriores fueron detenidas. Revisar los reportes del build.\n"
    )
    return message


def send_message(message: EmailMessage, config: dict, username: str, password: str) -> None:
    if not username or not password:
        raise ValueError("Faltan credenciales SMTP")
    if not isinstance(config, dict):
        raise ValueError("Configuración SMTP inválida")
    for field in ("host",):
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError("Configuración SMTP inválida")
    if type(config.get("port")) is not int or not 1 <= config["port"] <= 65535:
        raise ValueError("Puerto SMTP inválido")
    mode = config.get("tls", "starttls")
    context = ssl.create_default_context()
    host, port = config["host"], int(config["port"])
    if mode == "ssl":
        connection = smtplib.SMTP_SSL(host, port, timeout=15, context=context)
    elif mode == "starttls":
        connection = smtplib.SMTP(host, port, timeout=15)
    else:
        raise ValueError("SMTP requiere starttls o ssl")
    with connection as smtp:
        if mode == "starttls":
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
        smtp.login(username, password)
        refused = smtp.send_message(message)
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("to", "build", "commit", "environment", "stage", "log-url"):
        parser.add_argument("--" + field, required=True)
    parser.add_argument("--report", default="reports/notifications/status.json")
    args = parser.parse_args()
    status = {
        "build": args.build, "commit": args.commit, "environment": args.environment,
        "stage": args.stage, "log_url": args.log_url, "status": "failed",
    }
    try:
        config = json.loads(Path(os.environ["SMTP_CONFIG_FILE"]).read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("Configuración SMTP inválida")
        message = build_message(
            config["sender"], args.to, build=args.build, commit=args.commit,
            environment=args.environment, stage=args.stage, log_url=args.log_url,
        )
        send_message(message, config, os.environ.get("SMTP_USERNAME", ""), os.environ.get("SMTP_PASSWORD", ""))
        status["status"] = "accepted_by_smtp"
        print("El servidor SMTP aceptó la notificación; verificar recepción en el buzón.")
        return 0
    except (OSError, smtplib.SMTPException, ValueError, KeyError) as error:
        # No imprimir respuestas SMTP ni configuración: pueden contener información sensible.
        status["error_type"] = type(error).__name__
        print("No se pudo enviar la notificación SMTP. Revisar credenciales y conectividad.")
        return 1
    finally:
        report = Path(args.report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
