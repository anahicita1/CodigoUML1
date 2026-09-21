from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from autenticacion import Autenticacion
from cliente_api import ClienteAPI
from repositorio import RepositorioDB
from validacion import ValidadorIndicadores


def ejecutar() -> int:
    try:
        load_dotenv()

        autenticacion = Autenticacion()
        if not autenticacion.autenticar_consola():
            return 1

        db_path = Path(os.environ.get("DB_PATH", "ecotech_servicios.db"))
        repositorio = RepositorioDB(db_path)
        repositorio.inicializar()

        codigo = os.environ.get("API_INDICADOR", "dolar")
        cliente = ClienteAPI(
            base_url=os.environ.get("API_URL", "https://mindicador.cl/api"),
            timeout=int(os.environ.get("API_TIMEOUT", "5")),
        )

        datos = cliente.obtener_indicador(codigo)
        registros = ValidadorIndicadores.extraer_registros(datos)
        guardados = 0
        descartados = 0

        for registro in registros:
            if repositorio.crear_indicador(codigo, registro["fecha"], registro["valor"]):
                guardados += 1
            else:
                descartados += 1

        if not registros:
            respaldo = repositorio.listar_indicadores(codigo)
            descartados += 1
            print(f"API no disponible o sin datos válidos. Registros de respaldo: {len(respaldo)}.")

        print(f"Indicador procesado: {codigo}")
        print(f"Registros guardados: {guardados}")
        print(f"Registros descartados: {descartados}")
        return 0
    except sqlite3.Error as exc:
        print(f"Error controlado de SQLite: {exc}")
        return 1
    except (ValueError, OSError) as exc:
        print(f"Error controlado de configuración: {exc}")
        return 1
    except Exception as exc:
        print(f"Error controlado durante la ejecución: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(ejecutar())
