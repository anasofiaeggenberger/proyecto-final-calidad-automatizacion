"""Despliegue y cleanup limitados a recursos propios de un build."""

import argparse
import json
import os
import re
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OWNER_LABEL = "org.hospital.build-token"


def docker(*args: str, env: dict | None = None) -> str:
    return subprocess.check_output(["docker", *args], cwd=ROOT, env=env, text=True).strip()


def validate_project(project: str) -> None:
    if not re.fullmatch(r"hospital-build-[a-z0-9-]{8,80}", project):
        raise ValueError("El proyecto debe ser exclusivo de este build: hospital-build-...")


def base_url(address: str) -> str:
    parsed = urlsplit("http://" + address.strip())
    if parsed.hostname != "127.0.0.1" or not parsed.port or not 1 <= parsed.port <= 65535:
        raise ValueError("Docker debe publicar la API sólo en loopback con un puerto asignado")
    return f"http://127.0.0.1:{parsed.port}"


def environment(state: dict) -> dict:
    return {
        **os.environ, "APP_VERSION": state["version"], "BUILD_TOKEN": state["token"],
        "CI_PORT": "0", "STAGING_PORT": "0",
    }


def assert_owned(state: dict) -> None:
    """Comprueba etiquetas de TODOS los recursos que down podría retirar."""
    validate_project(state["project"])
    for kind, listing in (("container", ["ps", "-aq"]), ("network", ["network", "ls", "-q"])):
        ids = docker(*listing, "--filter", "label=com.docker.compose.project=" + state["project"]).split()
        if not ids:
            continue
        objects = json.loads(docker(kind, "inspect", *ids))
        for obj in objects:
            labels = obj["Config"]["Labels"] if kind == "container" else obj["Labels"]
            if labels.get(OWNER_LABEL) != state["token"]:
                raise RuntimeError("Cleanup rechazado: se encontró un recurso ajeno al build")


def deploy(project: str, ambient: str, version: str, report: Path) -> str:
    validate_project(project)
    if ambient not in ("ci", "staging") or not re.fullmatch(r"[a-f0-9]{40}", version):
        raise ValueError("Ambiente o SHA inválidos")
    report.mkdir(parents=True, exist_ok=True)
    state_path = report / "deployment.json"
    if state_path.exists():
        raise RuntimeError("No sobrescribir el estado de un despliegue anterior")
    # No adoptar proyectos que ya contengan recursos, aunque estén detenidos.
    for listing in (["ps", "-aq"], ["network", "ls", "-q"]):
        if docker(*listing, "--filter", "label=com.docker.compose.project=" + project):
            raise RuntimeError("El proyecto ya tiene recursos; elegir otro identificador")
    state = {"project": project, "ambient": ambient, "version": version, "token": uuid.uuid4().hex}
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    env = environment(state)
    # El estado se guarda antes de up para poder limpiar también un arranque parcial.
    docker("compose", "-p", project, "--profile", ambient, "up", "-d", "--no-build", "api-" + ambient, env=env)
    assert_owned(state)
    url = base_url(docker("compose", "-p", project, "port", "api-" + ambient, "8000", env=env))
    (report / "endpoint.txt").write_text(url + "\n", encoding="utf-8")
    print(f"Proyecto: {project}; ambiente: {ambient}; URL: {url}")
    return url


def cleanup(report: Path) -> None:
    state_path = report / "deployment.json"
    if not state_path.exists():
        print("Sin despliegue de este build; no se ejecuta Docker cleanup.")
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert_owned(state)  # Ante discrepancia no ejecutar down ni ocultar el fallo.
    env = environment(state)
    command = ["docker", "compose", "-p", state["project"], "--profile", state["ambient"]]
    with (report / "compose-logs.txt").open("w", encoding="utf-8") as log:
        subprocess.run([*command, "logs", "--no-color", "--tail", "200"],
                       cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    subprocess.run([*command, "down", "--remove-orphans"], cwd=ROOT, env=env, check=True)
    (report / "cleanup.json").write_text(
        json.dumps({"project": state["project"], "status": "removed"}) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["deploy", "cleanup"])
    parser.add_argument("--project")
    parser.add_argument("--environment", choices=["ci", "staging"])
    parser.add_argument("--version")
    parser.add_argument("--report-dir", type=Path, default=Path("reports/build"))
    args = parser.parse_args()
    try:
        if args.action == "deploy":
            deploy(args.project or "", args.environment or "", args.version or "", args.report_dir)
        else:
            cleanup(args.report_dir)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.CalledProcessError):
        print("La operación Docker falló; revisar logs y propiedad del proyecto.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
