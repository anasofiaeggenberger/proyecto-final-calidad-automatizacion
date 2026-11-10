"""Propiedad y ciclo de vida de recursos de CI; no usa Docker real."""

import json
from unittest.mock import MagicMock

import pytest

from scripts import gestionar_ambiente as deploy


def state(report):
    report.mkdir(parents=True)
    value = {"project": "hospital-build-abcdefgh", "ambient": "ci", "version": "a" * 40, "token": "own-token"}
    (report / "deployment.json").write_text(json.dumps(value))
    return value


def test_cleanup_sin_deploy_no_invoca_docker(tmp_path, monkeypatch):
    command = MagicMock()
    monkeypatch.setattr(deploy, "docker", command)
    monkeypatch.setattr(deploy.subprocess, "run", command)
    deploy.cleanup(tmp_path)
    command.assert_not_called()


def test_cleanup_rechaza_recursos_de_otro_build(tmp_path, monkeypatch):
    state(tmp_path / "build")
    monkeypatch.setattr(deploy, "docker", MagicMock(side_effect=[
        "other-container", json.dumps([{"Config": {"Labels": {deploy.OWNER_LABEL: "another-token"}}}])
    ]))
    command = MagicMock()
    monkeypatch.setattr(deploy.subprocess, "run", command)
    with pytest.raises(RuntimeError):
        deploy.cleanup(tmp_path / "build")
    command.assert_not_called()


def test_cleanup_comprueba_tambien_la_red(tmp_path, monkeypatch):
    state(tmp_path / "build")
    monkeypatch.setattr(deploy, "docker", MagicMock(side_effect=[
        "", "other-network", json.dumps([{"Labels": {deploy.OWNER_LABEL: "other-token"}}])
    ]))
    command = MagicMock()
    monkeypatch.setattr(deploy.subprocess, "run", command)
    with pytest.raises(RuntimeError):
        deploy.cleanup(tmp_path / "build")
    command.assert_not_called()


def test_deploy_no_adopta_un_proyecto_existente(tmp_path, monkeypatch):
    command = MagicMock(return_value="existing-container")
    monkeypatch.setattr(deploy, "docker", command)
    with pytest.raises(RuntimeError):
        deploy.deploy("hospital-build-abcdefgh", "ci", "a" * 40, tmp_path)
    assert not (tmp_path / "deployment.json").exists()
    assert command.call_count == 1


def test_arranque_parcial_guarda_estado_para_cleanup(tmp_path, monkeypatch):
    command = MagicMock(side_effect=["", "", RuntimeError("up failed")])
    monkeypatch.setattr(deploy, "docker", command)
    with pytest.raises(RuntimeError):
        deploy.deploy("hospital-build-abcdefgh", "ci", "a" * 40, tmp_path)
    value = json.loads((tmp_path / "deployment.json").read_text())
    assert value["project"] == "hospital-build-abcdefgh" and value["token"]


@pytest.mark.parametrize("project", ["hospital-queue", "", "../../otro", "hospital-build-X"])
def test_rechaza_proyectos_no_exclusivos(project):
    with pytest.raises(ValueError):
        deploy.validate_project(project)


@pytest.mark.parametrize("address", ["0.0.0.0:1234", "localhost:1234", "127.0.0.1:0"])
def test_rechaza_endpoint_sin_puerto_loopback(address):
    with pytest.raises(ValueError):
        deploy.base_url(address)


def test_descubre_puerto_dinamico_loopback():
    assert deploy.base_url("127.0.0.1:32123") == "http://127.0.0.1:32123"
