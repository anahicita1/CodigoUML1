from datetime import date, datetime
from contextlib import contextmanager
from functools import wraps
import sys
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st
# Desbloqueo temporal de sesión
st.session_state["autenticado"] = True
st.session_state["rol"] = "Administrador"
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from base_datos.conexion import ConexionBD
from autenticacion import Autenticacion
from modelos.administrador import Administrador
from modelos.departamento import Departamento
from modelos.empleado import Empleado
from modelos.informe import Informe
from modelos.proyecto import Proyecto
from modelos.registro_tiempo import RegistroTiempo
from servicios.clima import obtener_clima
from servicios.indicadores import obtener_indicador


st.set_page_config(page_title="EcoTech CRUD", page_icon="📊", layout="wide")


for clave, valor_inicial in {
    "autenticado": False,
    "rol": None,
    "seccion": "Empleados",
    "registro_empleado": None,
    "registro_proyecto": None,
    "mensaje": "",
}.items():
    st.session_state.setdefault(clave, valor_inicial)


def mostrar_login() -> None:
    st.title("EcoTech Solutions")
    st.subheader("Ingreso seguro al sistema")
    with st.form("formulario_login"):
        usuario = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Iniciar sesión"):
            autenticacion = Autenticacion()
            rol = autenticacion.obtener_rol(usuario.strip(), contrasena)
            if rol:
                st.session_state["autenticado"] = True
                st.session_state["rol"] = rol
                st.rerun()
            st.error("Usuario o contraseña incorrectos.")


if not st.session_state["autenticado"]:
    mostrar_login()
    st.stop()


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ecotech.db"


def inicializar_bd() -> ConexionBD:
    try:
        db = ConexionBD(str(DB_PATH))
        db.crear_tablas()
        return db
    except Exception as exc:
        st.error(f"Ocurrió un error inesperado: {exc}")
        return None


inicializar_bd()


@contextmanager
def conexion():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        if conn is not None:
            conn.close()


def consultar(sql: str, parametros=()) -> pd.DataFrame:
    try:
        with conexion() as conn:
            return pd.read_sql_query(sql, conn, params=parametros)
    except sqlite3.Error as exc:
        st.warning(f"Error de base de datos: {exc}")
        return pd.DataFrame()
    except Exception as exc:
        st.error(f"Ocurrió un error inesperado: {exc}")
        return pd.DataFrame()


def ejecutar(sql: str, parametros=()) -> bool:
    try:
        with conexion() as conn:
            conn.execute(sql, parametros)
            conn.commit()
        return True
    except sqlite3.IntegrityError as exc:
        st.warning(f"Error de integridad en la base de datos: {exc}")
        return False
    except sqlite3.Error as exc:
        st.warning(f"Error de base de datos: {exc}")
        return False
    except Exception as exc:
        st.error(f"Ocurrió un error inesperado: {exc}")
        return False


def mostrar_integridad(exc: sqlite3.IntegrityError) -> None:
    mensaje = str(exc).lower()
    if "unique" in mensaje or "primary key" in mensaje:
        st.warning("El ID o correo ya se encuentra registrado.")
    else:
        st.warning(f"Error de integridad en la base de datos: {exc}")


def moneda_clp(valor) -> str:
    if pd.isna(valor):
        return ""
    return f"$ {int(valor):,}".replace(",", ".")


@st.cache_data(ttl=300, show_spinner=False)
def cargar_indicador(codigo: str) -> dict:
    return obtener_indicador(codigo)


def fecha_chilena(fecha_iso: str | None) -> str:
    try:
        if not fecha_iso or fecha_iso == "respaldo-inicial":
            return datetime.now().strftime("%d/%m/%Y")
        return datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return datetime.now().strftime("%d/%m/%Y")


def valor_clp(valor: float) -> str:
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " CLP"


def proyecto_desde_fila(fila) -> Proyecto:
    return Proyecto(
        int(fila["ID"]), fila["Nombre"], fila["Descripción"], fila["Inicio"],
        float(fila["Presupuesto"]), fila["Fin estimado"] or "", fila["Fin real"] or "",
    )


def empleado_desde_fila(fila) -> Empleado:
    return Empleado(
        int(fila["ID"]), fila["Nombre"], fila["Correo"], fila["Contraseña"],
        fila["Dirección"] or "", fila["Teléfono"] or "", fila["Fecha contrato"] or "",
        float(fila["Salario"] or 0), fila["Cargo"] or "Empleado",
    )


def proteger_interfaz(funcion):
    @wraps(funcion)
    def envoltura(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except Exception as exc:
            st.error(f"Ocurrió un error inesperado: {exc}")
            return None

    return envoltura


def boton_eliminar(tabla: str, columna: str, titulo: str, opciones: list[int], clave: str) -> None:
    st.subheader(titulo)
    if not opciones:
        st.info("No hay registros disponibles para eliminar.")
        return

    with st.form(f"form_delete_{clave}"):
        registro_id = st.selectbox("Selecciona el ID", opciones, key=f"select_delete_{clave}")
        confirmar = st.checkbox("Confirmo que deseo eliminar este registro.", key=f"confirm_{clave}")
        enviado = st.form_submit_button("Eliminar")
        if enviado:
            if not confirmar:
                st.error("Debes confirmar la eliminación.")
                return
            try:
                ejecutar(f"DELETE FROM {tabla} WHERE {columna} = ?", (registro_id,))
                st.success("Registro eliminado correctamente.")
                st.rerun()
            except sqlite3.IntegrityError as exc:
                st.error(f"No se puede eliminar el registro: {exc}")


@proteger_interfaz
def formulario_empleados() -> None:
    st.header("Empleados")
    with st.form("crear_empleado", clear_on_submit=True):
        st.subheader("Registrar empleado")
        id_usuario = st.number_input("ID", min_value=1, step=1, key="empleado_id")
        nombre = st.text_input("Nombre")
        correo = st.text_input("Correo")
        contrasena = st.text_input("Contraseña cifrada", type="password")
        direccion = st.text_input("Dirección")
        telefono = st.text_input("Teléfono")
        fecha_contrato = st.date_input("Fecha de contrato", key="fecha_contrato")
        salario = st.number_input("Salario (CLP)", min_value=0, value=850000, step=10000, format="%d")
        cargo = st.text_input("Cargo", value="Empleado")
        enviado = st.form_submit_button("Registrar empleado")
        if enviado:
            try:
                empleado = Empleado(
                    int(id_usuario), nombre, correo, contrasena, direccion, telefono,
                    fecha_contrato.isoformat(), float(salario), cargo,
                )
                ejecutar(
                    "INSERT INTO usuarios (id_usuario, nombre, correo, contrasena_cifrada, "
                    "tipo_usuario, direccion, telefono, fecha_contrato, salario, cargo) "
                    "VALUES (?, ?, ?, ?, 'Empleado', ?, ?, ?, ?, ?)",
                    (empleado.id_usuario, empleado.nombre, empleado.correo,
                     empleado.contrasena_cifrada, empleado.direccion, empleado.telefono,
                     empleado.fecha_contrato, empleado.salario, empleado.cargo),
                )
                st.success("Empleado registrado correctamente.")
            except ValueError as exc:
                st.error(str(exc))
            except sqlite3.IntegrityError as exc:
                mostrar_integridad(exc)

    empleados = consultar(
        "SELECT id_usuario AS ID, nombre AS Nombre, correo AS Correo, cargo AS Cargo, "
        "salario AS Salario, telefono AS Teléfono FROM usuarios "
        "WHERE tipo_usuario = 'Empleado' ORDER BY id_usuario"
    )
    st.subheader("Listado de empleados")
    st.dataframe(empleados.style.format({"Salario": moneda_clp}), use_container_width=True, hide_index=True)

    col_update, col_delete = st.columns(2)
    with col_update:
        with st.form("actualizar_salario"):
            st.subheader("Actualizar salario")
            ids = empleados["ID"].tolist()
            seleccionado = st.selectbox("Empleado", ids) if ids else None
            nuevo_salario = st.number_input("Nuevo salario (CLP)", min_value=0, value=850000, step=10000, format="%d")
            if st.form_submit_button("Actualizar", disabled=not ids) and seleccionado is not None:
                ejecutar("UPDATE usuarios SET salario = ? WHERE id_usuario = ? AND tipo_usuario = 'Empleado'", (nuevo_salario, seleccionado))
                st.success("Salario actualizado.")
                st.rerun()
    with col_delete:
        boton_eliminar("usuarios", "id_usuario", "Eliminar empleado", empleados["ID"].tolist(), "empleado")


@proteger_interfaz
def formulario_administradores() -> None:
    st.header("Administradores")
    with st.form("crear_administrador", clear_on_submit=True):
        st.subheader("Registrar administrador")
        id_usuario = st.number_input("ID", min_value=1, step=1, key="admin_id")
        nombre = st.text_input("Nombre", key="admin_nombre")
        correo = st.text_input("Correo", key="admin_correo")
        contrasena = st.text_input("Contraseña cifrada", type="password", key="admin_password")
        nivel_acceso = st.number_input("Nivel de acceso", min_value=1, step=1, key="nivel_acceso")
        enviado = st.form_submit_button("Registrar administrador")
        if enviado:
            try:
                admin = Administrador(int(id_usuario), nombre, correo, contrasena, int(nivel_acceso))
                ejecutar(
                    "INSERT INTO usuarios (id_usuario, nombre, correo, contrasena_cifrada, tipo_usuario, nivel_acceso) "
                    "VALUES (?, ?, ?, ?, 'Administrador', ?)",
                    (admin.id_usuario, admin.nombre, admin.correo, admin.contrasena_cifrada, admin.nivel_acceso),
                )
                st.success("Administrador registrado correctamente.")
            except ValueError as exc:
                st.error(str(exc))
            except sqlite3.IntegrityError as exc:
                mostrar_integridad(exc)

    administradores = consultar(
        "SELECT id_usuario AS ID, nombre AS Nombre, correo AS Correo, nivel_acceso AS Nivel "
        "FROM usuarios WHERE tipo_usuario = 'Administrador' ORDER BY id_usuario"
    )
    st.subheader("Listado de administradores")
    st.dataframe(administradores, use_container_width=True, hide_index=True)
    col_update, col_delete = st.columns(2)
    with col_update:
        with st.form("actualizar_nivel"):
            st.subheader("Actualizar nivel de acceso")
            ids = administradores["ID"].tolist()
            seleccionado = st.selectbox("Administrador", ids) if ids else None
            nivel = st.number_input("Nuevo nivel", min_value=1, step=1)
            if st.form_submit_button("Actualizar", disabled=not ids) and seleccionado is not None:
                ejecutar("UPDATE usuarios SET nivel_acceso = ? WHERE id_usuario = ? AND tipo_usuario = 'Administrador'", (nivel, seleccionado))
                st.success("Nivel de acceso actualizado.")
                st.rerun()
    with col_delete:
        boton_eliminar("usuarios", "id_usuario", "Eliminar administrador", administradores["ID"].tolist(), "administrador")


@proteger_interfaz
def formulario_departamentos() -> None:
    st.header("Departamentos")
    with st.form("crear_departamento", clear_on_submit=True):
        st.subheader("Registrar departamento")
        id_depto = st.number_input("ID", min_value=1, step=1, key="depto_id")
        nombre = st.text_input("Nombre", key="depto_nombre")
        gerente = st.text_input("Gerente", value="Por asignar")
        if st.form_submit_button("Registrar departamento"):
            try:
                depto = Departamento(int(id_depto), nombre, gerente)
                ejecutar("INSERT INTO departamentos (id_depto, nombre, gerente) VALUES (?, ?, ?)", (depto.id_depto, depto.nombre, depto.gerente))
                st.success("Departamento registrado correctamente.")
            except ValueError as exc:
                st.error(str(exc))
            except sqlite3.IntegrityError as exc:
                mostrar_integridad(exc)
    departamentos = consultar("SELECT id_depto AS ID, nombre AS Nombre, gerente AS Gerente FROM departamentos ORDER BY id_depto")
    st.subheader("Listado de departamentos")
    st.dataframe(departamentos, use_container_width=True, hide_index=True)
    col_update, col_delete = st.columns(2)
    with col_update:
        with st.form("actualizar_gerente"):
            st.subheader("Actualizar gerente")
            ids = departamentos["ID"].tolist()
            seleccionado = st.selectbox("Departamento", ids) if ids else None
            gerente = st.text_input("Nuevo gerente")
            if st.form_submit_button("Actualizar", disabled=not ids) and seleccionado is not None:
                ejecutar("UPDATE departamentos SET gerente = ? WHERE id_depto = ?", (gerente, seleccionado))
                st.success("Gerente actualizado.")
                st.rerun()
    with col_delete:
        boton_eliminar("departamentos", "id_depto", "Eliminar departamento", departamentos["ID"].tolist(), "departamento")


@proteger_interfaz
def formulario_proyectos() -> None:
    st.header("Proyectos")
    with st.form("crear_proyecto", clear_on_submit=True):
        st.subheader("Registrar proyecto")
        id_proyecto = st.number_input("ID", min_value=1, step=1, key="proyecto_id")
        nombre = st.text_input("Nombre", key="proyecto_nombre")
        descripcion = st.text_area("Descripción")
        fecha_inicio = st.date_input("Fecha de inicio", key="fecha_inicio")
        fecha_fin_estimada = st.date_input("Fecha fin estimada", key="fecha_fin_estimada")
        proyecto_finalizado = st.checkbox("El proyecto ya finalizó")
        fecha_fin_real = st.date_input("Fecha fin real", value=date.today(), disabled=not proyecto_finalizado, key="fecha_fin_real")
        presupuesto = st.number_input("Presupuesto (CLP)", min_value=0, value=10000000, step=1000000, format="%d")
        if st.form_submit_button("Registrar proyecto"):
            try:
                if fecha_fin_estimada < fecha_inicio:
                    st.error("La fecha fin estimada no puede ser menor que la fecha de inicio.")
                    return
                fecha_real = fecha_fin_real.isoformat() if proyecto_finalizado else ""
                if proyecto_finalizado and fecha_fin_real < fecha_inicio:
                    st.error("La fecha fin real no puede ser menor que la fecha de inicio.")
                    return
                proyecto = Proyecto(
                    int(id_proyecto), nombre, descripcion, fecha_inicio.isoformat(), int(presupuesto),
                    fecha_fin_estimada.isoformat(), fecha_real,
                )
                ejecutar(
                    "INSERT INTO proyectos (id_proyecto, nombre, descripcion, fecha_inicio, presupuesto, "
                    "fecha_fin_estimada, fecha_fin_real) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (proyecto.id_proyecto, proyecto.nombre, proyecto.descripcion, proyecto.fecha_inicio,
                     proyecto.presupuesto, proyecto.fecha_fin_estimada, proyecto.fecha_fin_real or None),
                )
                st.success("Proyecto registrado correctamente.")
            except ValueError as exc:
                st.error(str(exc))
            except sqlite3.IntegrityError as exc:
                mostrar_integridad(exc)
    proyectos = consultar(
        "SELECT id_proyecto AS ID, nombre AS Nombre, descripcion AS Descripción, "
        "fecha_inicio AS Inicio, fecha_fin_estimada AS 'Fin estimado', "
        "fecha_fin_real AS 'Fin real', presupuesto AS Presupuesto "
        "FROM proyectos ORDER BY id_proyecto"
    )
    st.subheader("Listado de proyectos")
    st.dataframe(proyectos.style.format({"Presupuesto": moneda_clp}), use_container_width=True, hide_index=True)
    col_update, col_delete = st.columns(2)
    with col_update:
        with st.form("actualizar_presupuesto"):
            st.subheader("Actualizar presupuesto")
            ids = proyectos["ID"].tolist()
            seleccionado = st.selectbox("Proyecto", ids) if ids else None
            presupuesto = st.number_input("Nuevo presupuesto (CLP)", min_value=0, value=10000000, step=1000000, format="%d")
            if st.form_submit_button("Actualizar", disabled=not ids) and seleccionado is not None:
                ejecutar("UPDATE proyectos SET presupuesto = ? WHERE id_proyecto = ?", (presupuesto, seleccionado))
                st.success("Presupuesto actualizado.")
                st.rerun()
    with col_delete:
        boton_eliminar("proyectos", "id_proyecto", "Eliminar proyecto", proyectos["ID"].tolist(), "proyecto")

    st.subheader("Actualizar fecha fin real")
    proyectos_abiertos = proyectos[proyectos["Fin real"].isna() | (proyectos["Fin real"] == "")]
    if proyectos_abiertos.empty:
        st.info("No hay proyectos activos pendientes de cierre.")
    else:
        with st.form("actualizar_fecha_fin_real"):
            proyecto_id = st.selectbox("Proyecto activo", proyectos_abiertos["ID"].tolist())
            fecha_fin_real = st.date_input("Fecha fin real", value=date.today(), key="cierre_real")
            if st.form_submit_button("Marcar como finalizado"):
                fila = proyectos_abiertos[proyectos_abiertos["ID"] == proyecto_id].iloc[0]
                if fecha_fin_real < date.fromisoformat(fila["Inicio"]):
                    st.error("La fecha fin real no puede ser menor que la fecha de inicio.")
                else:
                    ejecutar("UPDATE proyectos SET fecha_fin_real = ? WHERE id_proyecto = ?", (fecha_fin_real.isoformat(), proyecto_id))
                    st.success("Proyecto marcado como finalizado.")
                    st.rerun()

    st.subheader("Asignación de empleados")
    empleados_proyecto = consultar(
        "SELECT id_usuario AS ID, nombre AS Nombre, correo AS Correo, "
        "contrasena_cifrada AS Contraseña, direccion AS Dirección, telefono AS Teléfono, "
        "fecha_contrato AS 'Fecha contrato', salario AS Salario, cargo AS Cargo "
        "FROM usuarios WHERE tipo_usuario = 'Empleado' ORDER BY nombre"
    )
    proyectos_activos = proyectos[proyectos["Fin real"].isna() | (proyectos["Fin real"] == "")]
    if empleados_proyecto.empty or proyectos_activos.empty:
        st.info("Se necesita al menos un empleado y un proyecto activo para crear asignaciones.")
    else:
        empleados_por_id = {int(fila["ID"]): fila for _, fila in empleados_proyecto.iterrows()}
        proyectos_por_id = {int(fila["ID"]): fila for _, fila in proyectos_activos.iterrows()}
        col_assign, col_unassign = st.columns(2)
        with col_assign:
            with st.form("asignar_empleado_proyecto"):
                empleado_id = st.selectbox(
                    "Empleado",
                    list(empleados_por_id),
                    format_func=lambda valor: f"{valor} - {empleados_por_id[valor]['Nombre']}",
                    key="asignar_empleado_id",
                )
                proyecto_id = st.selectbox(
                    "Proyecto activo",
                    list(proyectos_por_id),
                    format_func=lambda valor: f"{valor} - {proyectos_por_id[valor]['Nombre']}",
                    key="asignar_proyecto_id",
                )
                if st.form_submit_button("Asignar empleado"):
                    try:
                        proyecto = proyecto_desde_fila(proyectos_por_id[proyecto_id])
                        empleado = empleado_desde_fila(empleados_por_id[empleado_id])
                        existente = consultar(
                            "SELECT 1 FROM proyecto_empleados WHERE id_proyecto = ? AND id_usuario = ?",
                            (proyecto_id, empleado_id),
                        )
                        if not existente.empty:
                            st.warning("El empleado ya está asignado a este proyecto.")
                        elif proyecto.asignar_empleado(empleado):
                            ejecutar(
                                "INSERT INTO proyecto_empleados (id_proyecto, id_usuario) VALUES (?, ?)",
                                (proyecto_id, empleado_id),
                            )
                            st.success("Empleado asignado al proyecto.")
                            st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                    except sqlite3.IntegrityError as exc:
                        mostrar_integridad(exc)
        with col_unassign:
            with st.form("desasignar_empleado_proyecto"):
                empleado_id = st.selectbox(
                    "Empleado asignado",
                    list(empleados_por_id),
                    format_func=lambda valor: f"{valor} - {empleados_por_id[valor]['Nombre']}",
                    key="desasignar_empleado_id",
                )
                proyecto_id = st.selectbox(
                    "Proyecto",
                    list(proyectos_por_id),
                    format_func=lambda valor: f"{valor} - {proyectos_por_id[valor]['Nombre']}",
                    key="desasignar_proyecto_id",
                )
                if st.form_submit_button("Desasignar empleado"):
                    relacion = consultar(
                        "SELECT 1 FROM proyecto_empleados WHERE id_proyecto = ? AND id_usuario = ?",
                        (proyecto_id, empleado_id),
                    )
                    if relacion.empty:
                        st.warning("El empleado no está asignado a este proyecto.")
                    else:
                        proyecto = proyecto_desde_fila(proyectos_por_id[proyecto_id])
                        empleado = empleado_desde_fila(empleados_por_id[empleado_id])
                        proyecto.asignar_empleado(empleado)
                        if proyecto.desasignar_empleado(empleado):
                            ejecutar(
                                "DELETE FROM proyecto_empleados WHERE id_proyecto = ? AND id_usuario = ?",
                                (proyecto_id, empleado_id),
                            )
                            st.success("Empleado desasignado del proyecto.")
                            st.rerun()

    asignaciones = consultar(
        "SELECT pe.id_proyecto AS 'ID Proyecto', p.nombre AS Proyecto, "
        "pe.id_usuario AS 'ID Empleado', u.nombre AS Empleado "
        "FROM proyecto_empleados pe "
        "JOIN proyectos p ON p.id_proyecto = pe.id_proyecto "
        "JOIN usuarios u ON u.id_usuario = pe.id_usuario "
        "ORDER BY p.nombre, u.nombre"
    )
    st.dataframe(asignaciones, use_container_width=True, hide_index=True)


@proteger_interfaz
def formulario_registros() -> None:
    st.header("Registros de Tiempo")
    try:
        empleados = consultar(
            "SELECT id_usuario AS ID, nombre AS Nombre FROM usuarios "
            "WHERE tipo_usuario = 'Empleado' ORDER BY nombre"
        )
        proyectos = consultar(
            "SELECT id_proyecto AS ID, nombre AS Nombre FROM proyectos "
            "WHERE fecha_fin_real IS NULL OR fecha_fin_real = '' ORDER BY nombre"
        )
    except Exception as exc:
        st.error(f"Se produjo un error: {exc}")
        return

    ids_empleados = empleados["ID"].tolist()
    nombres_empleados = dict(zip(empleados["ID"], empleados["Nombre"]))
    ids_proyectos = proyectos["ID"].tolist()
    nombres_proyectos = dict(zip(proyectos["ID"], proyectos["Nombre"]))

    if not ids_empleados:
        st.warning("No hay registros disponibles")
    if not ids_proyectos:
        st.warning("No hay registros disponibles")

    with st.form("crear_registro", clear_on_submit=True):
        st.subheader("Registrar horas")
        usuario = st.selectbox(
            "Empleado",
            ids_empleados or ["sin_empleados"],
            format_func=lambda valor: (
                f"{valor} - {nombres_empleados[valor]}"
                if valor in nombres_empleados else "No hay empleados registrados"
            ),
            disabled=not ids_empleados,
            key="registro_empleado",
        )
        proyecto_id = st.selectbox(
            "Proyecto",
            ids_proyectos or ["sin_proyectos"],
            format_func=lambda valor: (
                f"{valor} - {nombres_proyectos[valor]}"
                if valor in nombres_proyectos else "No hay proyectos activos"
            ),
            disabled=not ids_proyectos,
            key="registro_proyecto",
        )
        fecha = st.date_input("Fecha", value=date.today())
        horas = st.number_input("Horas", min_value=0.5, max_value=24.0, value=8.0, step=0.5)
        descripcion = st.text_area("Descripción")
        if st.form_submit_button("Registrar horas", disabled=not (ids_empleados and ids_proyectos)):
            if usuario not in nombres_empleados or proyecto_id not in nombres_proyectos:
                st.error("Primero debes registrar un empleado y un proyecto activo.")
            else:
                try:
                    descripcion_final = descripcion or f"Horas trabajadas en el proyecto '{nombres_proyectos[proyecto_id]}'."
                    registro = RegistroTiempo(
                        0, int(usuario), fecha.isoformat(), float(horas), descripcion_final,
                        int(proyecto_id),
                    )
                    ejecutar(
                        "INSERT INTO registros_tiempo "
                        "(id_usuario, id_proyecto, fecha, horas, descripcion) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (registro.id_usuario, registro.id_proyecto, registro.fecha,
                         registro.horas, registro.descripcion),
                    )
                    st.success("Registro de tiempo guardado correctamente.")
                except ValueError as exc:
                    st.error(str(exc))
                except sqlite3.IntegrityError as exc:
                    mostrar_integridad(exc)
    registros = consultar(
        "SELECT r.id_registro AS ID, u.nombre AS Empleado, "
        "COALESCE(p.nombre, 'Sin proyecto') AS Proyecto, r.fecha AS Fecha, "
        "r.horas AS Horas, r.descripcion AS Descripción "
        "FROM registros_tiempo r "
        "JOIN usuarios u ON u.id_usuario = r.id_usuario "
        "LEFT JOIN proyectos p ON p.id_proyecto = r.id_proyecto "
        "ORDER BY r.fecha DESC, r.id_registro DESC"
    )
    st.subheader("Listado de registros")
    st.dataframe(registros, use_container_width=True, hide_index=True)
    ids = registros["ID"].tolist()
    if ids:
        with st.form("actualizar_registro"):
            st.subheader("Actualizar horas")
            seleccionado = st.selectbox("Registro", ids)
            horas = st.number_input("Nuevas horas", min_value=0.01, max_value=24.0, step=0.5)
            descripcion = st.text_input("Nueva descripción")
            if st.form_submit_button("Actualizar"):
                try:
                    RegistroTiempo(int(seleccionado), 0, "", float(horas), descripcion or "Registro de trabajo")
                    ejecutar("UPDATE registros_tiempo SET horas = ?, descripcion = ? WHERE id_registro = ?", (horas, descripcion or "Registro de trabajo", seleccionado))
                    st.success("Registro actualizado.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        boton_eliminar("registros_tiempo", "id_registro", "Eliminar registro", ids, "registro")


@proteger_interfaz
def formulario_informes() -> None:
    st.header("Informes")
    with st.form("crear_informe", clear_on_submit=True):
        st.subheader("Generar informe")
        id_informe = st.number_input("ID", min_value=1, step=1, key="informe_id")
        tipo = st.selectbox(
            "Tipo de informe",
            [
                "Resumen de Proyectos",
                "Horas Trabajadas por Empleado",
                "Control de Presupuesto",
                "Desempeño Departamental",
            ],
        )
        contenido = st.text_area("Contenido")
        fecha_generacion = st.date_input("Fecha de generación", value=date.today())
        formato = st.selectbox("Formato de exportación", ["PDF", "CSV", "Excel"])
        if st.form_submit_button("Generar informe"):
            try:
                informe = Informe(int(id_informe), tipo, contenido, fecha_generacion.isoformat(), formato)
                ejecutar("INSERT INTO informes (id_informe, tipo, contenido, fecha_generacion, formato_exportacion) VALUES (?, ?, ?, ?, ?)", (informe.id_informe, informe.tipo, informe.contenido, informe.fecha_generacion, informe.formato_exportacion))
                st.success("Informe registrado correctamente.")
            except ValueError as exc:
                st.error(str(exc))
            except sqlite3.IntegrityError as exc:
                mostrar_integridad(exc)
    informes = consultar("SELECT id_informe AS ID, tipo AS Tipo, contenido AS Contenido, fecha_generacion AS Fecha, formato_exportacion AS Formato FROM informes ORDER BY id_informe")
    st.subheader("Listado de informes")
    st.dataframe(informes, use_container_width=True, hide_index=True)
    ids = informes["ID"].tolist()
    if ids:
        with st.form("actualizar_informe"):
            st.subheader("Actualizar informe")
            seleccionado = st.selectbox("Informe", ids)
            contenido = st.text_area("Nuevo contenido")
            formato = st.selectbox("Nuevo formato", ["PDF", "Excel", "CSV"])
            if st.form_submit_button("Actualizar"):
                ejecutar("UPDATE informes SET contenido = ?, formato_exportacion = ? WHERE id_informe = ?", (contenido, formato, seleccionado))
                st.success("Informe actualizado.")
                st.rerun()
        boton_eliminar("informes", "id_informe", "Eliminar informe", ids, "informe")


st.title("EcoTech Solutions")

with st.sidebar:
    st.header("Navegación")
    st.subheader("Indicador económico")
    try:
        dolar = cargar_indicador("dolar")
        uf = cargar_indicador("uf")
        fechas = []
        usa_respaldo_local = False
        for indicador in (dolar, uf):
            if "error" in indicador:
                st.warning(indicador["error"])
            else:
                if indicador.get("fuente") == "respaldo SQLite":
                    usa_respaldo_local = True
                etiqueta = "Dólar Observado" if indicador["codigo"] == "dolar" else "UF"
                st.metric(etiqueta, valor_clp(indicador["valor"]))
                fechas.append(fecha_chilena(indicador["fecha"]))
        if usa_respaldo_local:
            st.warning("⚠️ Sin conexión a la API. Mostrando datos locales de SQLite.")
        if fechas:
            st.caption(f"Actualizado al {fechas[0]}")
    except Exception as exc:
        st.error(f"Ocurrió un error inesperado: {exc}")

    st.subheader("Clima de Valparaíso")
    try:
        clima = obtener_clima()
        if "error" in clima:
            st.warning(clima["error"])
        else:
            if clima.get("fuente") == "respaldo SQLite":
                st.warning("⚠️ Sin conexión a Open-Meteo. Mostrando clima local de SQLite.")
            st.metric("Temperatura", f"{clima['temperatura']:.1f} °C")
            st.metric("Humedad", f"{clima['humedad']:.0f} %")
    except Exception as exc:
        st.error(f"Ocurrió un error inesperado: {exc}")

    modulos = ["Empleados", "Proyectos", "Registros de Tiempo"]
    if st.session_state["rol"] == "Administrador":
        modulos = ["Empleados", "Administradores", "Departamentos", "Proyectos", "Registros de Tiempo", "Informes"]
    if st.session_state["seccion"] not in modulos:
        st.session_state["seccion"] = modulos[0]
    seccion = st.selectbox(
        "Módulo",
        modulos,
        key="seccion",
    )

if seccion == "Empleados":
    formulario_empleados()
elif seccion == "Administradores":
    formulario_administradores()
elif seccion == "Departamentos":
    formulario_departamentos()
elif seccion == "Proyectos":
    formulario_proyectos()
elif seccion == "Registros de Tiempo":
    formulario_registros()
else:
    formulario_informes()
