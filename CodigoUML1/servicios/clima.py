from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


CLIMA_URL = "https://api.open-meteo.com/v1/forecast"
LATITUD_CHILE = -33.0472
LONGITUD_CHILE = -71.6127


def obtener_clima() -> dict[str, Any]:
    parametros = {
        "latitude": LATITUD_CHILE,
        "longitude": LONGITUD_CHILE,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "timezone": "America/Santiago",
    }
    try:
        respuesta = requests.get(CLIMA_URL, params=parametros, timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
        actual = datos.get("current") if isinstance(datos, dict) else None
        if not isinstance(actual, dict):
            return _obtener_respaldo("La API de clima no devolvió datos actuales.")
        temperatura = actual.get("temperature_2m")
        humedad = actual.get("relative_humidity_2m")
        if not isinstance(temperatura, (int, float)) or not isinstance(humedad, (int, float)):
            return _obtener_respaldo("La respuesta climática no tiene valores válidos.")
        return {
            "temperatura": float(temperatura),
            "humedad": float(humedad),
            "fecha": actual.get("time") or datetime.now().isoformat(),
            "fuente": "Open-Meteo",
        }
    except requests.Timeout:
        return _obtener_respaldo("La consulta climática superó el límite de 5 segundos.")
    except requests.ConnectionError:
        return _obtener_respaldo("No fue posible conectarse con Open-Meteo.")
    except requests.RequestException as exc:
        return _obtener_respaldo(f"Open-Meteo devolvió un error HTTP: {exc}")
    except (ValueError, TypeError, AttributeError) as exc:
        return _obtener_respaldo(f"La respuesta climática no es válida: {exc}")


def _obtener_respaldo(motivo: str) -> dict[str, Any]:
    db_path = Path(os.getenv("DB_PATH", Path(__file__).resolve().parents[1] / "ecotech.db"))
    try:
        with sqlite3.connect(db_path) as conexion:
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS clima (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    temperatura REAL NOT NULL,
                    humedad REAL NOT NULL
                )
                """
            )
            conexion.execute(
                """
                INSERT INTO clima (fecha, temperatura, humedad)
                SELECT ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM clima)
                """,
                (datetime.now().isoformat(), 18.0, 65.0),
            )
            fila = conexion.execute(
                "SELECT fecha, temperatura, humedad FROM clima ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if fila is None:
            return {"error": f"{motivo} No existe respaldo climático."}
        return {
            "fecha": fila[0] or datetime.now().isoformat(),
            "temperatura": float(fila[1]),
            "humedad": float(fila[2]),
            "fuente": "respaldo SQLite",
            "advertencia": motivo,
        }
    except sqlite3.Error as exc:
        return {"error": f"{motivo} No fue posible leer SQLite: {exc}"}
