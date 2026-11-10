"""Ejecuta E2E con selección observable de suite/navegador y reportes."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["smoke", "regression"], default="regression")
    parser.add_argument("--browser", choices=["chromium", "firefox"], default="chromium")
    parser.add_argument("--base-url", default=os.environ.get("E2E_BASE_URL", ""))
    parser.add_argument("--report-dir", default="reports/e2e")
    args = parser.parse_args()

    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    selection = {
        "suite": args.suite, "browser": args.browser, "commit": sha,
        "url": args.base_url or "servidor HTTP local en puerto dinámico",
    }
    (report_dir / "selection.json").write_text(
        json.dumps(selection, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(selection, indent=2), flush=True)
    command = [
        sys.executable, "-m", "pytest", "tests/e2e", "-v", "--strict-markers",
        "-m", "e2e and smoke" if args.suite == "smoke" else "e2e",
        "--browser", args.browser,
        "--tracing", "retain-on-failure", "--screenshot", "only-on-failure",
        "--full-page-screenshot", "--output", str(report_dir / "artifacts"),
        "--junitxml", str(report_dir / "junit.xml"),
        "--html", str(report_dir / "report.html"), "--self-contained-html",
    ]
    env = {**os.environ, "E2E_REPORT_DIR": str(report_dir)}
    if args.base_url:
        env["E2E_BASE_URL"] = args.base_url
    return subprocess.call(command, cwd=ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
