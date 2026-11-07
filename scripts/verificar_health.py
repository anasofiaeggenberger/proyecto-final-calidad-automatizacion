"""Verifica que la instancia desplegada reporte su ambiente y versión por HTTP."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def consultar(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as respuesta:
        if respuesta.status != 200:
            raise RuntimeError(f"health respondió {respuesta.status}")
        return json.loads(respuesta.read().decode("utf-8"))


def esperar(url: str, limite: float) -> dict:
    fin = time.monotonic() + limite
    ultimo_error = "sin intentos"
    while time.monotonic() < fin:
        try:
            return consultar(url)
        except (urllib.error.URLError, OSError, RuntimeError, ValueError) as error:
            ultimo_error = str(error)
            time.sleep(1)
    raise SystemExit(f"health no respondió en {limite:.0f}s: {ultimo_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--ambiente", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--timeout", type=float, default=90.0)
    argumentos = parser.parse_args()

    cuerpo = esperar(argumentos.url, argumentos.timeout)
    print(f"health {argumentos.url} -> {json.dumps(cuerpo, ensure_ascii=False)}")

    errores = []
    if cuerpo.get("estado") != "ok":
        errores.append(f"estado={cuerpo.get('estado')!r}, se esperaba 'ok'")
    if cuerpo.get("ambiente") != argumentos.ambiente:
        errores.append(
            f"ambiente={cuerpo.get('ambiente')!r}, se esperaba {argumentos.ambiente!r}"
        )
    if cuerpo.get("version") != argumentos.version:
        errores.append(
            f"version={cuerpo.get('version')!r}, se esperaba {argumentos.version!r}"
        )

    if errores:
        for error in errores:
            print(f"health inválido: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
