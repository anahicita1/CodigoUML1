import sqlite3
from base_datos.conexion import ConexionBD
from modelos.empleado import Empleado
from modelos.administrador import Administrador
from modelos.departamento import Departamento
from modelos.proyecto import Proyecto
from modelos.registro_tiempo import RegistroTiempo
from modelos.informe import Informe


# =====================================================================
# CRUD: EMPLEADOS (tabla usuarios, tipo_usuario = 'Empleado')
# =====================================================================
def registrar_empleado_db(conexion_bd: ConexionBD, empleado: Empleado):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO usuarios (id_usuario, nombre, correo, contrasena_cifrada, tipo_usuario,
                                   direccion, telefono, fecha_contrato, salario, cargo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (empleado.id_usuario, empleado.nombre, empleado.correo, empleado.contrasena_cifrada, 'Empleado',
              empleado.direccion, empleado.telefono, empleado.fecha_contrato, empleado.salario, empleado.cargo))
        conn.commit()
        print(f"CRUD (Create): Empleado '{empleado.nombre}' registrado exitosamente en BD.")
    except sqlite3.IntegrityError:
        print(f"Error de Integridad: Ya existe un usuario con el ID {empleado.id_usuario} o correo '{empleado.correo}'.")
    except sqlite3.Error as e:
        print(f"Error en BD al registrar empleado: {e}")
    finally:
        conn.close()


def consultar_empleados_db(conexion_bd: ConexionBD):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, nombre, correo, cargo, salario, telefono FROM usuarios WHERE tipo_usuario = 'Empleado'")
        registros = cursor.fetchall()

        print("\n📋 CRUD (Read): Lista de Empleados en Base de Datos:")
        if not registros:
            print("   (No hay empleados registrados)")
        for reg in registros:
            print(f"   ID: {reg[0]} | Nombre: {reg[1]} | Correo: {reg[2]} | Cargo: {reg[3]} | Salario: ${reg[4]:,.2f} | Tel: {reg[5]}")
    except sqlite3.Error as e:
        print(f"Error al consultar empleados: {e}")
    finally:
        conn.close()


def actualizar_salario_db(conexion_bd: ConexionBD, id_usuario: int, nuevo_salario: float):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET salario = ? WHERE id_usuario = ? AND tipo_usuario = 'Empleado'", (nuevo_salario, id_usuario))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"\nCRUD (Update): Salario del empleado ID {id_usuario} actualizado a ${nuevo_salario:,.2f}.")
        else:
            print(f"\nCRUD (Update): No se encontró un empleado con ID {id_usuario}.")
    except sqlite3.Error as e:
        print(f"Error al actualizar salario: {e}")
    finally:
        conn.close()


def eliminar_empleado_db(conexion_bd: ConexionBD, id_usuario: int):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = ? AND tipo_usuario = 'Empleado'", (id_usuario,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"\nCRUD (Delete): Empleado con ID {id_usuario} eliminado de la base de datos.")
        else:
            print(f"\nCRUD (Delete): No se encontró un empleado con ID {id_usuario} para eliminar.")
    except sqlite3.Error as e:
        print(f"Error al eliminar empleado: {e}")
    finally:
        conn.close()


# =====================================================================
# CRUD: ADMINISTRADORES (tabla usuarios, tipo_usuario = 'Administrador')
# =====================================================================
def registrar_administrador_db(conexion_bd: ConexionBD, admin: Administrador):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO usuarios (id_usuario, nombre, correo, contrasena_cifrada, tipo_usuario, nivel_acceso)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin.id_usuario, admin.nombre, admin.correo, admin.contrasena_cifrada, 'Administrador', admin.nivel_acceso))
        conn.commit()
        print(f"CRUD (Create): Administrador '{admin.nombre}' registrado exitosamente en BD.")
    except sqlite3.IntegrityError:
        print(f"Error de Integridad: Ya existe un usuario con el ID {admin.id_usuario} o correo '{admin.correo}'.")
    except sqlite3.Error as e:
        print(f"Error en BD al registrar administrador: {e}")
    finally:
        conn.close()


# =====================================================================
# CRUD: DEPARTAMENTOS
# =====================================================================
def registrar_departamento_db(conexion_bd: ConexionBD, depto: Departamento):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO departamentos (id_depto, nombre, gerente) VALUES (?, ?, ?)",
                       (depto.id_depto, depto.nombre, depto.gerente))
        conn.commit()
        print(f"CRUD (Create): Departamento '{depto.nombre}' registrado exitosamente en BD.")
    except sqlite3.IntegrityError:
        print(f"Error de Integridad: Ya existe un departamento con ID {depto.id_depto}.")
    except sqlite3.Error as e:
        print(f"Error en BD al registrar departamento: {e}")
    finally:
        conn.close()


def consultar_departamentos_db(conexion_bd: ConexionBD):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_depto, nombre, gerente FROM departamentos")
        registros = cursor.fetchall()
        print("\n📋 CRUD (Read): Lista de Departamentos en Base de Datos:")
        for reg in registros:
            print(f"   ID: {reg[0]} | Nombre: {reg[1]} | Gerente: {reg[2]}")
    except sqlite3.Error as e:
        print(f"Error al consultar departamentos: {e}")
    finally:
        conn.close()


def actualizar_gerente_departamento_db(conexion_bd: ConexionBD, id_depto: int, nuevo_gerente: str):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE departamentos SET gerente = ? WHERE id_depto = ?", (nuevo_gerente, id_depto))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"\nCRUD (Update): Gerente del departamento ID {id_depto} actualizado a '{nuevo_gerente}'.")
        else:
            print(f"\nCRUD (Update): No se encontró un departamento con ID {id_depto}.")
    except sqlite3.Error as e:
        print(f"Error al actualizar departamento: {e}")
    finally:
        conn.close()


def eliminar_departamento_db(conexion_bd: ConexionBD, id_depto: int):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM departamentos WHERE id_depto = ?", (id_depto,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"\nCRUD (Delete): Departamento con ID {id_depto} eliminado de la base de datos.")
        else:
            print(f"\nCRUD (Delete): No se encontró un departamento con ID {id_depto} para eliminar.")
    except sqlite3.Error as e:
        print(f"Error al eliminar departamento: {e}")
    finally:
        conn.close()


# =====================================================================
# CRUD: PROYECTOS
# =====================================================================
def registrar_proyecto_db(conexion_bd: ConexionBD, proy: Proyecto):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO proyectos (id_proyecto, nombre, descripcion, fecha_inicio, presupuesto,
                                   fecha_fin_estimada, fecha_fin_real)
            VALUES (?, ?, ?, ?, ?, ?, ?)
          ''', (proy.id_proyecto, proy.nombre, proy.descripcion, proy.fecha_inicio,
              proy.presupuesto, proy.fecha_fin_estimada, proy.fecha_fin_real))
        conn.commit()
        print(f"CRUD (Create): Proyecto '{proy.nombre}' registrado exitosamente en BD.")
    except sqlite3.IntegrityError:
        print(f"Error de Integridad: Ya existe un proyecto con ID {proy.id_proyecto}.")
    except sqlite3.Error as e:
        print(f"Error en BD al registrar proyecto: {e}")
    finally:
        conn.close()


def consultar_proyectos_db(conexion_bd: ConexionBD):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_proyecto, nombre, fecha_inicio, fecha_fin_estimada, fecha_fin_real, presupuesto FROM proyectos")
        registros = cursor.fetchall()
        print("\n📋 CRUD (Read): Lista de Proyectos en Base de Datos:")
        for reg in registros:
            print(f"   ID: {reg[0]} | Nombre: {reg[1]} | Inicio: {reg[2]} | Fin estimado: {reg[3]} | Fin real: {reg[4]} | Presupuesto: ${reg[5]:,.2f}")
    except sqlite3.Error as e:
        print(f"Error al consultar proyectos: {e}")
    finally:
        conn.close()


def actualizar_presupuesto_proyecto_db(conexion_bd: ConexionBD, id_proyecto: int, nuevo_presupuesto: float):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE proyectos SET presupuesto = ? WHERE id_proyecto = ?", (nuevo_presupuesto, id_proyecto))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"\nCRUD (Update): Presupuesto del proyecto ID {id_proyecto} actualizado a ${nuevo_presupuesto:,.2f}.")
        else:
            print(f"\nCRUD (Update): No se encontró un proyecto con ID {id_proyecto}.")
    except sqlite3.Error as e:
        print(f"Error al actualizar proyecto: {e}")
    finally:
        conn.close()


def actualizar_fechas_proyecto_db(conexion_bd: ConexionBD, id_proyecto: int,
                                  fecha_fin_estimada: str, fecha_fin_real: str = ""):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE proyectos SET fecha_fin_estimada = ?, fecha_fin_real = ? WHERE id_proyecto = ?",
            (fecha_fin_estimada, fecha_fin_real or None, id_proyecto),
        )
        conn.commit()
        if cursor.rowcount > 0:
            print(f"\nCRUD (Update): Fechas del proyecto ID {id_proyecto} actualizadas.")
        else:
            print(f"\nCRUD (Update): No se encontró un proyecto con ID {id_proyecto}.")
    except sqlite3.Error as e:
        print(f"Error al actualizar fechas del proyecto: {e}")
    finally:
        conn.close()


def eliminar_proyecto_db(conexion_bd: ConexionBD, id_proyecto: int):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proyectos WHERE id_proyecto = ?", (id_proyecto,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"\nCRUD (Delete): Proyecto con ID {id_proyecto} eliminado de la base de datos.")
        else:
            print(f"\nCRUD (Delete): No se encontró un proyecto con ID {id_proyecto} para eliminar.")
    except sqlite3.Error as e:
        print(f"Error al eliminar proyecto: {e}")
    finally:
        conn.close()


# =====================================================================
# CRUD: REGISTROS DE TIEMPO
# =====================================================================
def registrar_registro_tiempo_db(conexion_bd: ConexionBD, registro: RegistroTiempo):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        # id_registro es AUTOINCREMENT en la BD: no forzamos el id local del objeto,
        # dejamos que SQLite asigne el identificador real de la fila.
        cursor.execute('''
            INSERT INTO registros_tiempo (id_usuario, id_proyecto, fecha, horas, descripcion)
            VALUES (?, ?, ?, ?, ?)
        ''', (registro.id_usuario, registro.id_proyecto, registro.fecha,
              registro.horas, registro.descripcion))
        conn.commit()
        print(f"CRUD (Create): Registro de tiempo del usuario {registro.id_usuario} guardado en BD.")
    except sqlite3.IntegrityError:
        print(f"Error de Integridad: Ya existe un registro de tiempo idéntico para el usuario "
              f"{registro.id_usuario} en la fecha {registro.fecha} con esa misma descripción.")
    except sqlite3.Error as e:
        print(f"Error en BD al registrar tiempo: {e}")
    finally:
        conn.close()


def consultar_registros_tiempo_db(conexion_bd: ConexionBD):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id_registro, r.id_usuario, r.id_proyecto, p.nombre,
                   r.fecha, r.horas, r.descripcion
            FROM registros_tiempo r
            LEFT JOIN proyectos p ON p.id_proyecto = r.id_proyecto
        """)
        registros = cursor.fetchall()
        print("\n📋 CRUD (Read): Registros de Tiempo en Base de Datos:")
        for reg in registros:
            print(f"   ID: {reg[0]} | Usuario: {reg[1]} | Proyecto: {reg[2]} - {reg[3]} | Fecha: {reg[4]} | Horas: {reg[5]} | {reg[6]}")
    except sqlite3.Error as e:
        print(f"Error al consultar registros de tiempo: {e}")
    finally:
        conn.close()


# =====================================================================
# CRUD: INFORMES
# =====================================================================
def registrar_informe_db(conexion_bd: ConexionBD, informe: Informe):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO informes (id_informe, tipo, contenido, fecha_generacion, formato_exportacion)
            VALUES (?, ?, ?, ?, ?)
        ''', (informe.id_informe, informe.tipo, informe.contenido, informe.fecha_generacion, informe.formato_exportacion))
        conn.commit()
        print(f"CRUD (Create): Informe '{informe.tipo}' registrado exitosamente en BD.")
    except sqlite3.IntegrityError:
        print(f"Error de Integridad: Ya existe un informe con ID {informe.id_informe}.")
    except sqlite3.Error as e:
        print(f"Error en BD al registrar informe: {e}")
    finally:
        conn.close()


def consultar_informes_db(conexion_bd: ConexionBD):
    conn = conexion_bd.obtener_conexion()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_informe, tipo, fecha_generacion, formato_exportacion FROM informes")
        registros = cursor.fetchall()
        print("\n📋 CRUD (Read): Informes en Base de Datos:")
        for reg in registros:
            print(f"   ID: {reg[0]} | Tipo: {reg[1]} | Fecha: {reg[2]} | Formato: {reg[3]}")
    except sqlite3.Error as e:
        print(f"Error al consultar informes: {e}")
    finally:
        conn.close()


def main():
    print("=" * 65)
    print("       SISTEMA DE GESTIÓN ECOTECH SOLUTIONS (POO SEGURO)       ")
    print("=" * 65)

    db = ConexionBD()
    db.crear_tablas()
    print("-" * 65)

    # --- Pruebas de validación y manejo de excepciones ---
    print("\n--- PRUEBAS DE SEGURIDAD Y VALIDACIÓN DE CLASES ---")
    try:
        print("Intentando crear un empleado con correo inválido...")
        Empleado(99, "Error User", "correo_invalido", "pass123", "Av. Caso 123", "+569000", "2026-01-01", 500000.0, "Tester")
    except ValueError as ve:
        print(f"Excepción capturada correctamente: {ve}")

    try:
        print("Intentando crear un empleado con salario negativo...")
        Empleado(98, "Salario Mal", "test@ecotech.cl", "pass123", "Av. Caso 123", "+569000", "2026-01-01", -100.0, "Tester")
    except ValueError as ve:
        print(f"Excepción capturada correctamente: {ve}")

    try:
        print("Intentando crear un empleado con contraseña de menos de 6 caracteres...")
        Empleado(97, "Clave Corta", "corta@ecotech.cl", "ab", "Av. Caso 123", "+569000", "2026-01-01", 100000.0, "Tester")
    except ValueError as ve:
        print(f"Excepción capturada correctamente: {ve}")

    print("-" * 65)

    # --- Creación de objetos POO fieles al UML ---
    print("\n--- CREACIÓN DE OBJETOS POO (FIDELIDAD UML) ---")
    emp1 = Empleado(1, "Anahí Vargas", "anahi@ecotech.cl", "hash_seguro_123", "Av. Valparaíso 456", "+56911112222", "2026-03-01", 850000.0, "Desarrolladora Lead")
    emp2 = Empleado(2, "Natalia Trejo", "ntrejo@ecotech.cl", "hash_seguro_456", "Calle Viña 789", "+56933334444", "2026-03-01", 820000.0, "Arquitecta de Software")
    admin1 = Administrador(100, "Natalia Martinez", "nmartinez@ecotech.cl", "admin_pass_789", 5)

    dept1 = Departamento(10, "Tecnologías de la Información", gerente="Natalia Martinez")
    dept1.agregar_empleado(emp1)
    dept1.agregar_empleado(emp2)

    proy1 = Proyecto(1, "Plataforma EcoTech", "Sistema de Gestión Sustentable", "2026-09-01", 15000000.0)
    proy1.asignar_empleado(emp1)

    # registrar_horas ahora crea un RegistroTiempo real (composición Empleado -> RegistroTiempo)
    emp1.registrar_horas("2026-09-10", 8, proy1)
    print(f"Registros de tiempo de {emp1.nombre}: {len(emp1.obtener_registros_tiempo())}")

    inf1 = Informe(500, "Rendimiento Mensual", "Resumen de horas desarrolladas por EcoTech", "2026-09-10", "PDF")
    inf1.exportar_pdf()
    inf1.exportar_excel()

    # Antes nunca se llamaban estos dos métodos del Administrador:
    admin1.registrar_nuevo_empleado(emp2)
    admin1.genera_reporte(inf1)  # ahora sí queda guardado en admin1.obtener_informes()

    emp1.iniciar_sesion()
    admin1.iniciar_sesion()

    print(f"Departamento asignado a {emp1.nombre}: {emp1.departamento.nombre}")  # antes esto habría sido None

    print("-" * 65)

    # --- Operaciones CRUD en SQLite (ahora cubriendo las 5 tablas, no solo empleados) ---
    print("\n--- OPERACIONES CRUD EN BASE DE DATOS (SQLITE) ---")
    registrar_empleado_db(db, emp1)
    registrar_empleado_db(db, emp2)
    registrar_administrador_db(db, admin1)
    registrar_departamento_db(db, dept1)
    registrar_proyecto_db(db, proy1)
    registrar_informe_db(db, inf1)
    for registro in emp1.obtener_registros_tiempo():
        registrar_registro_tiempo_db(db, registro)

    consultar_empleados_db(db)
    consultar_departamentos_db(db)
    consultar_proyectos_db(db)
    consultar_informes_db(db)
    consultar_registros_tiempo_db(db)

    actualizar_salario_db(db, id_usuario=1, nuevo_salario=950000.0)
    consultar_empleados_db(db)

    eliminar_empleado_db(db, id_usuario=2)
    consultar_empleados_db(db)

    # --- Demostración de CRUD completo (Update/Delete) en Departamentos y Proyectos ---
    print("\n--- CRUD COMPLETO: DEPARTAMENTOS Y PROYECTOS ---")
    dept_temporal = Departamento(11, "Soporte Técnico", gerente="Por asignar")
    registrar_departamento_db(db, dept_temporal)
    actualizar_gerente_departamento_db(db, id_depto=11, nuevo_gerente="Anahí Vargas")
    consultar_departamentos_db(db)
    eliminar_departamento_db(db, id_depto=11)
    consultar_departamentos_db(db)

    proy_temporal = Proyecto(2, "Auditoría Interna", "Revisión de procesos 2026", "2026-10-01", 2000000.0)
    registrar_proyecto_db(db, proy_temporal)
    actualizar_presupuesto_proyecto_db(db, id_proyecto=2, nuevo_presupuesto=2500000.0)
    consultar_proyectos_db(db)
    eliminar_proyecto_db(db, id_proyecto=2)
    consultar_proyectos_db(db)

    print("\n" + "=" * 65)
    print("         EJECUCIÓN FINALIZADA Y VERIFICADA CON ÉXITO          ")
    print("=" * 65)


if __name__ == "__main__":
    main()
