from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from repositorio import RepositorioDB


class ClienteAPI:
    """Cliente HTTP seguro para consultar indicadores económicos."""

    def __init__(self, base_url: str | None = None, timeout: int = 5) -> None:
        self.base_url = (base_url or os.getenv("API_URL", "https://mindicador.cl/api")).rstrip("/")
        self.timeout = 5

    def obtener_indicador(self, codigo: str) -> dict[str, Any] | None:
        """Devuelve JSON remoto o el último respaldo local si la API falla."""
        url = f"{self.base_url}/{codigo}"
        try:
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            datos = respuesta.json()
            return datos if isinstance(datos, dict) else None
        except requests.Timeout:
            print(f"Aviso: la consulta a {url} superó el límite obligatorio de 5 segundos.")
        except requests.ConnectionError:
            print(f"Aviso: no fue posible conectarse con {url}; se usará el respaldo local.")
        except requests.RequestException as exc:
            print(f"Aviso: la API respondió con un error controlado: {exc}")
        except ValueError as exc:
            print(f"Aviso: la API no devolvió JSON válido: {exc}")
        return self._obtener_respaldo_local(codigo)

    def _obtener_respaldo_local(self, codigo: str) -> dict[str, Any] | None:
        db_path = Path(os.getenv("DB_PATH", "ecotech_servicios.db"))
        try:
            repositorio = RepositorioDB(db_path)
            repositorio.inicializar_indicadores_por_defecto()
            registro = repositorio.obtener_ultimo_indicador(codigo)
            if registro is None:
                return None
            fecha_respaldo = registro[2]
            if not fecha_respaldo or fecha_respaldo == "respaldo-inicial":
                fecha_respaldo = datetime.now().isoformat()
            return {
                "codigo": codigo,
                "nombre": "Dólar observado" if codigo == "dolar" else "Unidad de Fomento",
                "unidad_medida": "Pesos",
                "serie": [{"fecha": fecha_respaldo, "valor": registro[3]}],
                "fuente": "respaldo SQLite",
            }
        except Exception as exc:
            print(f"Aviso: no fue posible leer el respaldo SQLite: {exc}")
            return None

    def obtener_serie(self, codigo: str) -> list[dict[str, Any]]:
        datos = self.obtener_indicador(codigo)
        if not datos:
            return []
        serie = datos.get("serie")
        return serie if isinstance(serie, list) else []
