"""Acceso compartido de DataOK mediante sesión firmada en cookie HttpOnly."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    """Verifica un hash scrypt sin conservar la contraseña en código."""
    try:
        esquema, n, r, p, sal, digest = hash_guardado.split("$")
        if esquema != "scrypt":
            return False
        calculado = hashlib.scrypt(
            clave.encode("utf-8"), salt=base64.urlsafe_b64decode(sal),
            n=int(n), r=int(r), p=int(p), dklen=len(base64.urlsafe_b64decode(digest)),
        )
        return hmac.compare_digest(calculado, base64.urlsafe_b64decode(digest))
    except (TypeError, ValueError):
        return False


def crear_token(usuario: str, secreto: str, duracion_segundos: int) -> str:
    ahora = int(time.time())
    carga = json.dumps({"sub": usuario, "iat": ahora, "exp": ahora + duracion_segundos}, separators=(",", ":")).encode()
    cuerpo = base64.urlsafe_b64encode(carga).rstrip(b"=")
    firma = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).digest()
    return f"{cuerpo.decode()}.{base64.urlsafe_b64encode(firma).rstrip(b'=').decode()}"


def leer_token(token: str | None, secreto: str) -> str | None:
    if not token or "." not in token:
        return None
    try:
        cuerpo, firma = token.encode().split(b".", 1)
        esperada = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).digest()
        recibida = base64.urlsafe_b64decode(firma + b"=" * (-len(firma) % 4))
        datos = json.loads(base64.urlsafe_b64decode(cuerpo + b"=" * (-len(cuerpo) % 4)))
        if not hmac.compare_digest(esperada, recibida) or int(datos["exp"]) < time.time():
            return None
        return str(datos["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def generar_secreto() -> str:
    return secrets.token_urlsafe(48)
