"""Genera variables seguras para la única cuenta compartida de DataOK.

Ejemplo:
    python scripts/generar_credenciales_acceso.py --usuario dataok
"""
from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import secrets


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera configuración de acceso DataOK")
    parser.add_argument("--usuario", required=True, help="Nombre de la cuenta compartida")
    args = parser.parse_args()
    clave = getpass.getpass("Clave inicial (mínimo 12 caracteres): ")
    confirmacion = getpass.getpass("Repite la clave: ")
    if len(clave) < 12:
        raise SystemExit("La clave debe tener al menos 12 caracteres.")
    if clave != confirmacion:
        raise SystemExit("Las claves no coinciden.")
    sal = secrets.token_bytes(16)
    n, r, p = 2**14, 8, 1
    digest = hashlib.scrypt(clave.encode("utf-8"), salt=sal, n=n, r=r, p=p)
    hash_seguro = "$".join((
        "scrypt", str(n), str(r), str(p),
        base64.urlsafe_b64encode(sal).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    ))
    print("\nGuarda estas líneas como secretos del servidor (no en el repositorio):")
    print("ACCESS_ENABLED=true")
    print(f"ACCESS_USUARIO={args.usuario}")
    print(f"ACCESS_CLAVE_HASH={hash_seguro}")
    print(f"ACCESS_SECRETO={secrets.token_urlsafe(48)}")
    print("ACCESS_DURACION_HORAS=12")


if __name__ == "__main__":
    main()
