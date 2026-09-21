from __future__ import annotations

from datetime import datetime
from typing import Any


class ValidadorIndicadores:
    """Valida y normaliza respuestas de indicadores externos."""

    @staticmethod
    def validar_respuesta(datos: Any) -> bool:
        if not isinstance(datos, dict):
            return False
        serie = datos.get("serie")
        return isinstance(serie, list) and bool(serie)

    @staticmethod
    def extraer_registros(datos: Any) -> list[dict[str, Any]]:
        if not ValidadorIndicadores.validar_respuesta(datos):
            return []
        registros: list[dict[str, Any]] = []
        for elemento in datos.get("serie", []):
            if not isinstance(elemento, dict):
                continue
            valor = elemento.get("valor")
            fecha = elemento.get("fecha")
            if not isinstance(valor, (int, float)) or valor is None:
                continue
            if not isinstance(fecha, str):
                continue
            try:
                datetime.fromisoformat(fecha.replace("Z", "+00:00"))
            except ValueError:
                continue
            if 0 < float(valor) < 1_000_000_000:
                registros.append({"fecha": fecha, "valor": float(valor)})
        return registros
