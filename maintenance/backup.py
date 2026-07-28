"""Backup completo de la base de datos superstore usando pg_dump."""

import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

BACKUP_DIR = Path.home() / "backups" / "superstore"
RETENTION_DAYS = 30
DB_NAME = os.getenv("DB_NAME", "superstore")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "lizandro")


def backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = BACKUP_DIR / f"{DB_NAME}_{timestamp}.dump"
    log.info("Iniciando backup → %s", filename)

    result = subprocess.run([
        "pg_dump", "-h", DB_HOST, "-U", DB_USER,
        "--format=custom",
        f"--file={filename}",
        DB_NAME,
    ], capture_output=True, text=True)

    if result.returncode == 0:
        size_mb = filename.stat().st_size / (1024 * 1024)
        log.info("Backup completado: %.1f MB — %s", size_mb, filename)
    else:
        log.error("Backup falló: %s", result.stderr)
        raise SystemExit(1)


def verify():
    log.info("Verificando integridad del backup ...")
    backups = sorted(BACKUP_DIR.glob(f"{DB_NAME}_*.dump"))
    if not backups:
        log.warning("No se encontraron backups")
        return
    latest = backups[-1]
    result = subprocess.run(
        ["pg_restore", "--list", str(latest)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        log.info("Backup íntegro: %s", latest.name)
    else:
        log.error("Backup corrupto: %s", result.stderr)


def cleanup():
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    removed = 0
    for f in BACKUP_DIR.glob(f"{DB_NAME}_*.dump"):
        ts_str = f.stem.replace(f"{DB_NAME}_", "")
        try:
            ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            if ts < cutoff:
                f.unlink()
                removed += 1
        except ValueError:
            pass
    log.info("Limpieza: %d backups eliminados (retención %d días)", removed, RETENTION_DAYS)


def list_backups():
    backups = sorted(BACKUP_DIR.glob(f"{DB_NAME}_*.dump"))
    for b in backups:
        size_mb = b.stat().st_size / (1024 * 1024)
        print(f"  {b.name}  ({size_mb:.1f} MB)")
    return backups


if __name__ == "__main__":
    backup()
    verify()
    cleanup()
    print("\nBackups disponibles:")
    list_backups()
