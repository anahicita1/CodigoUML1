import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


API_URL = "https://mindicador.cl/api"


def obtener_indicador(codigo: str = "dolar") -> dict[str, Any]:
    """Obtiene un indicador económico vigente desde mindicador.cl.

    La función devuelve un diccionario con ``error`` cuando el servicio
    externo no está disponible o responde con datos inválidos, para que la
    interfaz pueda continuar funcionando sin depender de la red.
    """
    try:
        respuesta = requests.get(f"{API_URL}/{codigo}", timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
        serie = datos.get("serie")
        if not isinstance(serie, list) or not serie or "valor" not in serie[0]:
            return _obtener_respaldo(codigo, f"La API no devolvió un valor válido para {codigo}.")
        return {
            "codigo": codigo,
            "nombre": datos.get("nombre", codigo.capitalize()),
            "unidad": datos.get("unidad_medida", "Pesos"),
            "valor": float(serie[0]["valor"]),
            "fecha": serie[0].get("fecha", "Sin fecha"),
        }
    except requests.Timeout:
        return _obtener_respaldo(codigo, "La consulta del indicador superó el límite de 5 segundos.")
    except requests.ConnectionError:
        return _obtener_respaldo(codigo, "No fue posible conectarse con el servicio de indicadores.")
    except requests.RequestException as exc:
        return _obtener_respaldo(codigo, f"No fue posible consultar el indicador externo: {exc}")
    except (ValueError, TypeError, AttributeError) as exc:
        return _obtener_respaldo(codigo, f"La respuesta del indicador no es válida: {exc}")


def _obtener_respaldo(codigo: str, motivo: str) -> dict[str, Any]:
    """Consulta SQLite y si es necesario crea valores mínimos de respaldo."""
    db_path = Path(os.getenv("DB_PATH", Path(__file__).resolve().parents[1] / "ecotech.db"))
    valores = {"dolar": 950.0, "uf": 38000.0}
    try:
        with sqlite3.connect(db_path) as conexion:
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS indicadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    valor REAL NOT NULL,
                    UNIQUE (codigo, fecha)
                )
                """
            )
            conexion.execute(
                "INSERT OR IGNORE INTO indicadores (codigo, fecha, valor) VALUES (?, ?, ?)",
                (codigo, "respaldo-inicial", valores.get(codigo, 0.0)),
            )
            fila = conexion.execute(
                """
                SELECT fecha, valor FROM indicadores
                WHERE codigo = ?
                ORDER BY CASE WHEN fecha = ? THEN 0 ELSE 1 END DESC, fecha DESC
                LIMIT 1
                """,
                (codigo, "respaldo-inicial"),
            ).fetchone()
        if fila is None:
            return {"error": f"{motivo} No existe respaldo para {codigo}."}
        fecha_respaldo = fila[0]
        if not fecha_respaldo or fecha_respaldo == "respaldo-inicial":
            fecha_respaldo = datetime.now().isoformat()
        return {
            "codigo": codigo,
            "nombre": "Dólar observado" if codigo == "dolar" else "Unidad de Fomento",
            "unidad": "Pesos",
            "valor": float(fila[1]),
            "fecha": fecha_respaldo,
            "fuente": "respaldo SQLite",
            "advertencia": motivo,
        }
    except sqlite3.Error as exc:
        return {"error": f"{motivo} No fue posible leer SQLite: {exc}"}
