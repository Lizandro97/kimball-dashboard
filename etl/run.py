"""Orquestador ETL: ejecuta extract → transform → load en secuencia."""

import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)
SCRIPTS_DIR = Path(__file__).parent


def run_step(name: str, script: str) -> bool:
    log.info("Iniciando %s ...", name)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script)],
        capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        log.info("  %s", line)
    if result.stderr:
        for line in result.stderr.splitlines():
            log.warning("  %s", line)
    if result.returncode != 0:
        log.error("%s falló (código %d)", name, result.returncode)
        return False
    log.info("%s completado OK", name)
    return True


def main():
    steps = [
        ("Extracción", "extract.py"),
        ("Transformación", "transform.py"),
        ("Carga dimensional", "load.py"),
    ]
    for name, script in steps:
        if not run_step(name, script):
            sys.exit(1)
    log.info("Pipeline ETL completado exitosamente")


if __name__ == "__main__":
    main()
