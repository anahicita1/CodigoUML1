from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


class RepositorioDB:
    """Repositorio SQLite con consultas parametrizadas y transacciones seguras."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)

    def _conexion(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.db_path)
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    def inicializar(self) -> None:
        with closing(self._conexion()) as conexion:
            with conexion:
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
                self._sembrar_indicadores_por_defecto(conexion)

    def _sembrar_indicadores_por_defecto(self, conexion: sqlite3.Connection) -> None:
        """Garantiza un respaldo local para Dólar y UF cuando no hay datos."""
        cantidad = conexion.execute("SELECT COUNT(*) FROM indicadores").fetchone()[0]
        if cantidad:
            return
        fecha_actual = datetime.now().isoformat()
        conexion.executemany(
            """
            INSERT OR IGNORE INTO indicadores (codigo, fecha, valor)
            VALUES (?, ?, ?)
            """,
            (
                ("dolar", fecha_actual, 950.0),
                ("uf", fecha_actual, 38000.0),
            ),
        )

    def inicializar_indicadores_por_defecto(self) -> None:
        """Asegura la existencia de los valores mínimos de respaldo."""
        self.inicializar()

    def crear_indicador(self, codigo: str, fecha: str, valor: float) -> bool:
        with closing(self._conexion()) as conexion:
            try:
                with conexion:
                    conexion.execute(
                        "INSERT INTO indicadores (codigo, fecha, valor) VALUES (?, ?, ?)",
                        (codigo, fecha, valor),
                    )
                return True
            except sqlite3.IntegrityError:
                return False

    def listar_indicadores(self, codigo: str | None = None) -> list[tuple]:
        with closing(self._conexion()) as conexion:
            if codigo is None:
                cursor = conexion.execute(
                    "SELECT id, codigo, fecha, valor FROM indicadores ORDER BY fecha DESC"
                )
            else:
                cursor = conexion.execute(
                    "SELECT id, codigo, fecha, valor FROM indicadores WHERE codigo = ? ORDER BY fecha DESC",
                    (codigo,),
                )
            return cursor.fetchall()

    def obtener_ultimo_indicador(self, codigo: str) -> tuple | None:
        with closing(self._conexion()) as conexion:
            cursor = conexion.execute(
                """
                SELECT id, codigo, fecha, valor
                FROM indicadores
                WHERE codigo = ?
                ORDER BY CASE WHEN fecha = ? THEN 0 ELSE 1 END DESC, fecha DESC
                LIMIT 1
                """,
                (codigo, "respaldo-inicial"),
            )
            return cursor.fetchone()

    def actualizar_indicador(self, registro_id: int, valor: float) -> bool:
        with closing(self._conexion()) as conexion:
            with conexion:
                cursor = conexion.execute(
                    "UPDATE indicadores SET valor = ? WHERE id = ?",
                    (valor, registro_id),
                )
            return cursor.rowcount > 0

    def eliminar_indicador(self, registro_id: int) -> bool:
        with closing(self._conexion()) as conexion:
            with conexion:
                cursor = conexion.execute(
                    "DELETE FROM indicadores WHERE id = ?",
                    (registro_id,),
                )
            return cursor.rowcount > 0
