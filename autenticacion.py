from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path


class Autenticacion:
    """Autenticación con hashes PBKDF2-SHA256 almacenados en configuración."""

    ALGORITMO = "pbkdf2_sha256"
    ITERACIONES = 310_000

    def __init__(self, usuario: str | None = None, contrasena_hash: str | None = None) -> None:
        self.usuarios = {
            usuario or os.environ.get("AUTH_USERNAME", ""): {
                "hash": contrasena_hash or os.environ.get("AUTH_PASSWORD_HASH", ""),
                "rol": "Administrador",
            },
            os.environ.get("EMPLOYEE_USERNAME", ""): {
                "hash": os.environ.get("EMPLOYEE_PASSWORD_HASH", ""),
                "rol": "Empleado",
            },
        }
        self.usuarios = {nombre: datos for nombre, datos in self.usuarios.items() if nombre and datos["hash"]}

    @classmethod
    def generar_hash(cls, contrasena: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", contrasena.encode("utf-8"), salt, cls.ITERACIONES
        )
        return f"{cls.ALGORITMO}${cls.ITERACIONES}${salt.hex()}${digest.hex()}"

    @classmethod
    def verificar_hash(cls, contrasena: str, hash_almacenado: str) -> bool:
        try:
            algoritmo, iteraciones, salt_hex, digest_hex = hash_almacenado.split("$", 3)
            if algoritmo != cls.ALGORITMO:
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                contrasena.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iteraciones),
            )
            return hmac.compare_digest(digest.hex(), digest_hex)
        except (ValueError, TypeError):
            return False

    def obtener_rol(self, usuario: str, contrasena: str) -> str | None:
        datos = self.usuarios.get(usuario)
        if datos and self.verificar_hash(contrasena, datos["hash"]):
            return datos["rol"]
        return None

    def verificar(self, usuario: str, contrasena: str) -> bool:
        return self.obtener_rol(usuario, contrasena) is not None

    def autenticar_consola(self) -> bool:
        usuario = input("Usuario: ").strip()
        contrasena = input("Contraseña: ")
        if self.verificar(usuario, contrasena):
            return True
        print("Autenticación rechazada.")
        return False
