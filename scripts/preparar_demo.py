"""Aplica o revierte una falla real, exclusivamente en una rama demo/."""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {"unit": "domain/patient.py", "integration": "api/routes.py", "e2e": "templates/index.html"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["apply", "revert"])
    parser.add_argument("layer", choices=FILES)
    args = parser.parse_args()
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip()
    if not branch.startswith("demo/"):
        parser.error("Crea primero una rama demo/<nombre> desde el commit entregado.")
    target = FILES[args.layer]
    if args.action == "apply":
        if subprocess.call(["git", "diff", "--quiet", "HEAD", "--", target], cwd=ROOT):
            parser.error("El archivo ya tiene cambios. Consérvalos antes de aplicar la falla.")
    patch = ROOT / "demo" / "fallas" / (args.layer + ".patch")
    flags = ["--reverse"] if args.action == "revert" else []
    check = subprocess.run(["git", "apply", "--check", *flags, str(patch)], cwd=ROOT)
    if check.returncode:
        return check.returncode
    result = subprocess.run(["git", "apply", *flags, str(patch)], cwd=ROOT)
    if result.returncode == 0:
        print(f"{args.action}: {args.layer}; archivo: {target}. Revisa git diff antes del commit.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
