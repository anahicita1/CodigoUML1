import sqlite3
from contextlib import contextmanager


class ConexionBD:
    def __init__(self, db_name="ecotech.db"):
        self.db_name = db_name

    def obtener_conexion(self):
        try:
            conexion = sqlite3.connect(self.db_name)
            # SQLite NO valida las FOREIGN KEY por defecto: hay que activarlo
            # explícitamente en cada conexión, si no, la integridad referencial
            # entre registros_tiempo/usuarios queda solo "de mentira" en el CREATE TABLE.
            conexion.execute("PRAGMA foreign_keys = ON")
            return conexion
        except sqlite3.Error as e:
            print(f"Error al conectar con SQLite: {e}")
            return None

    @contextmanager
    def conexion_segura(self):
        conexion = None
        try:
            conexion = sqlite3.connect(self.db_name)
            conexion.execute("PRAGMA foreign_keys = ON")
            yield conexion
            conexion.commit()
        except sqlite3.Error:
            if conexion is not None:
                conexion.rollback()
            raise
        finally:
            if conexion is not None:
                conexion.close()

    def crear_tablas(self):
        conexion = self.obtener_conexion()
        if not conexion:
            return

        cursor = conexion.cursor()

        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id_usuario INTEGER PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    correo TEXT NOT NULL UNIQUE,
                    contrasena_cifrada TEXT NOT NULL,
                    tipo_usuario TEXT NOT NULL,
                    direccion TEXT,
                    telefono TEXT,
                    fecha_contrato TEXT,
                    salario REAL,
                    cargo TEXT,
                    nivel_acceso INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS departamentos (
                    id_depto INTEGER PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    gerente TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proyectos (
                    id_proyecto INTEGER PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    fecha_inicio TEXT,
                    presupuesto REAL NOT NULL,
                    fecha_fin_estimada TEXT,
                    fecha_fin_real TEXT
                )
            ''')

            columnas_proyectos = {
                fila[1] for fila in cursor.execute("PRAGMA table_info(proyectos)")
            }
            if "fecha_fin_estimada" not in columnas_proyectos:
                cursor.execute("ALTER TABLE proyectos ADD COLUMN fecha_fin_estimada TEXT")
            if "fecha_fin_real" not in columnas_proyectos:
                cursor.execute("ALTER TABLE proyectos ADD COLUMN fecha_fin_real TEXT")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registros_tiempo (
                    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_usuario INTEGER NOT NULL,
                    id_proyecto INTEGER,
                    fecha TEXT NOT NULL,
                    horas REAL NOT NULL,
                    descripcion TEXT,
                    FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario),
                    FOREIGN KEY (id_proyecto) REFERENCES proyectos (id_proyecto),
                    UNIQUE (id_usuario, fecha, descripcion)
                )
            ''')

            columnas_registros = {
                fila[1] for fila in cursor.execute("PRAGMA table_info(registros_tiempo)")
            }
            if "id_proyecto" not in columnas_registros:
                cursor.execute("ALTER TABLE registros_tiempo RENAME TO registros_tiempo_antiguos")
                cursor.execute('''
                    CREATE TABLE registros_tiempo (
                        id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_usuario INTEGER NOT NULL,
                        id_proyecto INTEGER,
                        fecha TEXT NOT NULL,
                        horas REAL NOT NULL,
                        descripcion TEXT,
                        FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario),
                        FOREIGN KEY (id_proyecto) REFERENCES proyectos (id_proyecto),
                        UNIQUE (id_usuario, fecha, descripcion)
                    )
                ''')
                cursor.execute('''
                    INSERT INTO registros_tiempo
                        (id_registro, id_usuario, fecha, horas, descripcion)
                    SELECT id_registro, id_usuario, fecha, horas, descripcion
                    FROM registros_tiempo_antiguos
                ''')
                cursor.execute("DROP TABLE registros_tiempo_antiguos")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proyecto_empleados (
                    id_proyecto INTEGER NOT NULL,
                    id_usuario INTEGER NOT NULL,
                    PRIMARY KEY (id_proyecto, id_usuario),
                    FOREIGN KEY (id_proyecto) REFERENCES proyectos (id_proyecto) ON DELETE CASCADE,
                    FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS informes (
                    id_informe INTEGER PRIMARY KEY,
                    tipo TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    fecha_generacion TEXT,
                    formato_exportacion TEXT
                )
            ''')

            conexion.commit()
            print("Base de datos e infraestructura de tablas verificada con éxito.")
        except sqlite3.Error as e:
            print(f"Error al estructurar las tablas: {e}")
        finally:
            conexion.close()
