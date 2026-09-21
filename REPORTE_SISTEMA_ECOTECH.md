# EcoTech Solutions
## Reporte técnico y guía de defensa oral individual

**Fecha de defensa:** 23 de septiembre de 2026  
**Asignatura:** Programación Orientada a Objetos Segura  
**Proyecto:** Sistema de Gestión Integral EcoTech Solutions

> **Criterio de lectura:** este reporte distingue evidencia implementada, evidencia verificable en el código y extensiones técnicas propuestas para completar la rúbrica. No se presenta como implementada una función que no exista en el repositorio.

---

## 1. Resumen ejecutivo, arquitectura y estado del sistema

### 1.1 Objetivo y alcance

EcoTech Solutions centraliza la gestión de empleados, administradores, departamentos, proyectos, asignaciones, registros de tiempo, informes e indicadores económicos. La solución combina programación orientada a objetos, SQLite, consultas parametrizadas, consumo HTTP con `requests`, validación de entradas y una interfaz web con Streamlit.

El sistema aborda los problemas de duplicidad de identificadores, pérdida de asignaciones al reiniciar, ausencia de trazabilidad de horas, registros inconsistentes y dependencia de valores económicos introducidos manualmente. La aplicación dispone de dos flujos relacionados:

1. **Aplicación web CRUD:** `CodigoUML1/app.py`, con seis módulos y panel lateral de Dólar y UF.
2. **Flujo modular de integración:** `main.py`, `autenticacion.py`, `cliente_api.py`, `validacion.py` y `repositorio.py`, que demuestra configuración externa, autenticación, consulta de API, validación, persistencia y respaldo local.

### 1.2 Arquitectura por capas

| Capa | Implementación real | Responsabilidad |
|---|---|---|
| Presentación | `CodigoUML1/app.py` | Formularios, tablas, navegación, mensajes y métricas Streamlit. |
| Dominio | `CodigoUML1/modelos/*.py` | Entidades UML, herencia, encapsulamiento, asociaciones y reglas de negocio. |
| Persistencia | `CodigoUML1/base_datos/conexion.py`, `repositorio.py` | Esquema SQLite, CRUD, transacciones, claves foráneas y respaldo. |
| Integración | `cliente_api.py`, `CodigoUML1/servicios/indicadores.py` | Peticiones HTTP, JSON, timeout, errores y degradación offline. |
| Configuración y seguridad | `main.py`, `autenticacion.py`, `.env.example`, `.gitignore` | Variables de entorno, verificación de credenciales y exclusión de secretos. |

### 1.3 Flujo principal

En `app.py`, Streamlit inicializa la base con `ConexionBD.crear_tablas()`, carga el módulo seleccionado en `st.session_state["seccion"]` y ejecuta un formulario. El formulario convierte la entrada en un objeto de dominio, por ejemplo `Empleado(...)` o `RegistroTiempo(...)`; el constructor y sus propiedades validan los datos antes de persistirlos. La operación SQL se ejecuta con una tupla de parámetros, se confirma la transacción y se actualiza la vista con `st.rerun()`.

El panel lateral consulta `obtener_indicador("dolar")` y `obtener_indicador("uf")`. La respuesta se normaliza, se presenta con `st.metric` y se transforma a fecha chilena. Si la red falla, `indicadores.py` consulta SQLite y entrega el valor local junto con `fuente: "respaldo SQLite"`; la interfaz muestra una advertencia visible.

En el flujo de la raíz, `main.py` ejecuta `load_dotenv()`, autentica con `Autenticacion`, crea `RepositorioDB`, consulta `ClienteAPI`, filtra mediante `ValidadorIndicadores` y guarda registros válidos. Cuando no hay respuesta utilizable, conserva la continuidad leyendo indicadores locales.

### 1.4 Estado de implementación y pruebas de defensa

**Implementado y demostrable:** seis módulos CRUD; tabla puente `proyecto_empleados`; FKs activadas; consultas `?`; `INSERT`, `SELECT`, `UPDATE`, `DELETE`; confirmación previa de borrado; `ValueError` en reglas de dominio; `requests` con `timeout=5`; `raise_for_status()`; capturas de red; JSON validado; fallback SQLite; `.env`; hashes PBKDF2-SHA256 con salt; login Streamlit con `st.session_state` y `st.stop()`; roles Administrador/Empleado; cierre de sesión; Open-Meteo con temperatura, humedad y fallback SQLite; `requirements.txt`; mensajes de error y advertencia.

**Estado de cierre:** las tres brechas de seguridad, sesión y clima están implementadas y fueron verificadas mediante compilación, pruebas de hashes, control de acceso web, simulación de fallas de red y consulta de datos climáticos. La aplicación mantiene conexiones SQLite por operación, cerradas mediante gestores de contexto; no necesita compartir una conexión global ni `check_same_thread=False`.

---

## 2. Distribución técnica para la defensa: tres integrantes

### Integrante 1: POO, UML y base de datos

**Archivos:** `CodigoUML1/modelos/usuario.py`, `empleado.py`, `administrador.py`, `departamento.py`, `proyecto.py`, `registro_tiempo.py`, `informe.py`, `CodigoUML1/base_datos/conexion.py`, `repositorio.py` y `CodigoUML1/app.py`.

#### Mapeo exacto de UML a Python

- **Clase abstracta:** `class Usuario(ABC)` expresa que `Usuario` define el contrato común; `@abstractmethod` obliga a implementar `iniciar_sesion()` y `cerrar_sesion()`.
- **Herencia:** `class Empleado(Usuario)` y `class Administrador(Usuario)` reutilizan el constructor y las propiedades de la clase base. `super().__init__(...)` inicializa la parte heredada.
- **Encapsulamiento:** los datos se almacenan con doble guion bajo, por ejemplo `self.__salario`, `self.__proyectos` y `self.__registros_tiempo`. Python aplica name mangling para impedir el acceso directo accidental.
- **Acceso controlado:** `@property` define el getter y `@salario.setter` define la modificación validada. Así, `empleado.salario = nuevo_valor` pasa por la regla que rechaza valores negativos.
- **Asociación:** `self.__departamento = None`, `self.__proyectos = []` y los métodos `asignar_proyecto()`/`obtener_proyectos()` representan referencias entre objetos.
- **Composición:** `Empleado.registrar_horas()` crea un `RegistroTiempo` y lo incorpora a `self.__registros_tiempo`. El objeto compuesto pertenece al empleado en el modelo de dominio.
- **Polimorfismo:** cada subclase implementa las operaciones abstractas de sesión con su propio comportamiento.

#### Asociaciones, composición y tabla puente

En memoria, una relación de muchos a muchos se representa mediante listas: `Proyecto.__empleados` y `Empleado.__proyectos`. `Proyecto.asignar_empleado()` actualiza ambas listas, evitando una asociación unidireccional inconsistente. Esa representación se pierde al cerrar el proceso, por lo que la persistencia usa la tabla `proyecto_empleados` con columnas `id_proyecto` e `id_usuario`, PK compuesta y dos FKs.

La interfaz inserta con `INSERT INTO proyecto_empleados ... VALUES (?, ?)` y elimina con `DELETE ... WHERE id_proyecto = ? AND id_usuario = ?`. La consulta de lectura usa `JOIN` entre la tabla puente, `proyectos` y `usuarios`, reconstruyendo en pantalla la relación UML. `ON DELETE CASCADE` evita filas huérfanas cuando se elimina un proyecto o usuario.

La composición de registros de tiempo se persiste en `registros_tiempo`: `id_usuario` y `id_proyecto` son FKs, y la aplicación recupera la asociación con `JOIN`. La restricción `UNIQUE (id_usuario, fecha, descripcion)` previene duplicados lógicos.

#### Conexión y esquema SQLite

El patrón base es:

```python
conexion = sqlite3.connect(self.db_name)
conexion.execute("PRAGMA foreign_keys = ON")
```

`sqlite3.connect()` abre o crea el archivo indicado. `PRAGMA foreign_keys = ON` se ejecuta en cada conexión porque SQLite no activa las claves foráneas por defecto; esto hace efectivas las restricciones declaradas en `CREATE TABLE`.

En Streamlit, una conexión compartida entre hilos requeriría:

```python
sqlite3.connect(DB_PATH, check_same_thread=False)
```

El parámetro permite que la conexión no sea rechazada al utilizarse desde otro hilo. **En la implementación actual no se usa**, porque `app.py` abre una conexión nueva dentro de cada `with conexion()` y la cierra al terminar, y `ConexionBD` aplica el mismo aislamiento por operación. Esta decisión evita compartir objetos de conexión entre ejecuciones. Si se adopta una conexión cacheada o global para optimizar, `check_same_thread=False` debe acompañarse de serialización, transacciones breves y acceso controlado.

`conexion_segura()` usa `try/except/finally`: confirma con `commit()`, revierte con `rollback()` ante `sqlite3.Error` y cierra siempre el recurso.

#### CRUD completo con parámetros

1. **Create:** el formulario construye el objeto validado y ejecuta `INSERT INTO ... VALUES (?, ?, ...)` con una tupla, por ejemplo `(empleado.id_usuario, empleado.nombre, ...)`. Los signos `?` separan SQL de datos y evitan concatenación.
2. **Read:** `consultar()` ejecuta `SELECT` con parámetros opcionales y `pandas.read_sql_query`; el repositorio usa `fetchall()` para listados y `fetchone()` para un registro, como el último indicador.
3. **Update:** el formulario selecciona un ID y ejecuta `UPDATE tabla SET campo = ? WHERE id = ?`, confirma la transacción y vuelve a cargar la vista.
4. **Delete:** `boton_eliminar()` muestra una casilla de confirmación. Solo después de marcarla ejecuta `DELETE FROM tabla WHERE columna = ?`; el usuario recibe éxito o error y la vista se actualiza.

Las tuplas parametrizadas también aparecen en `RepositorioDB.crear_indicador()`, `listar_indicadores()`, `actualizar_indicador()` y `eliminar_indicador()`. La captura explícita de `sqlite3.IntegrityError` comunica PK/UNIQUE/FK duplicadas o inválidas; `sqlite3.OperationalError` debe capturarse de forma explícita en la capa de infraestructura para informar problemas de archivo, tabla o SQL. En la interfaz, el código actual captura la familia `sqlite3.Error` para consulta y ejecución; la defensa debe nombrar `IntegrityError` y `OperationalError` como especializaciones relevantes, no confundirlas con `ValueError` de dominio.

### Integrante 2: APIs, resiliencia y flujo de datos

**Archivos:** `cliente_api.py`, `CodigoUML1/servicios/indicadores.py`, `validacion.py`, `repositorio.py` y la sección de indicadores de `CodigoUML1/app.py`.

#### Indicadores económicos y contrato HTTP

El endpoint real es `https://mindicador.cl/api/{codigo}`, con `codigo` igual a `dolar` o `uf`. La llamada es `requests.get(url, timeout=5)`. Antes de leer `response.json()`, `respuesta.raise_for_status()` comprueba el estado:

- Un **200 OK** no lanza excepción y permite validar el JSON.
- Un **4xx Client Error** lanza `requests.HTTPError`: la solicitud o sus parámetros son rechazados por el servidor.
- Un **5xx Server Error** también lanza `requests.HTTPError`: el servicio remoto falló. Ambos casos entran en el respaldo mediante `requests.RequestException`.

Las capturas explícitas son `requests.Timeout`, `requests.ConnectionError`, `requests.RequestException` y, en la capa de validación, errores de tipo/valor (`ValueError`, `TypeError`, `AttributeError`). Las excepciones específicas aparecen antes que la general para conservar el diagnóstico: timeout, conexión, HTTP y finalmente otras fallas de la biblioteca.

El JSON esperado contiene `serie`, una lista cuyo primer elemento posee `valor` y `fecha`. `indicadores.py` verifica `isinstance(serie, list)`, presencia de `valor` y convierte el valor a `float`. `ValidadorIndicadores.extraer_registros()` filtra elementos no diccionario, fechas no ISO, valores no numéricos y montos fuera del rango permitido.

#### Segunda API de clima: implementación Open-Meteo

El módulo `CodigoUML1/servicios/clima.py` implementa Open-Meteo sin API key
para las coordenadas de Valparaíso (`-33.0472`, `-71.6127`):

```python
CLIMA_URL = "https://api.open-meteo.com/v1/forecast"
parametros = {
    "latitude": latitud,
    "longitude": longitud,
    "current": "temperature_2m,relative_humidity_2m,weather_code",
}
respuesta = requests.get(CLIMA_URL, params=parametros, timeout=5)
respuesta.raise_for_status()
datos = respuesta.json()
actual = datos.get("current", {})
```

El adaptador devuelve `temperatura`, `humedad`, `fecha` y `fuente`, utiliza
`timeout=5`, `raise_for_status()` y captura explícitamente las excepciones de
red. La barra lateral muestra las métricas climáticas junto a Dólar y UF. El
fallback crea la tabla `clima` y conserva una lectura local controlada.

#### Degradación y continuidad operativa

Ante timeout, desconexión, HTTP 4xx/5xx o JSON inválido, el sistema no detiene el panel: `_obtener_respaldo()` consulta SQLite, crea la tabla `indicadores` si es necesario e inserta valores mínimos (`dolar=950.0`, `uf=38000.0`) mediante `INSERT OR IGNORE`. La interfaz conserva las métricas y muestra `fuente: "respaldo SQLite"` y una advertencia. Esto reduce la dependencia de disponibilidad de terceros, mantiene trazabilidad del origen y permite operar en modo offline.

La misma estrategia se aplica al clima: se lee el último registro local si la
API falla y se informa al usuario que se está usando SQLite. La integración y
su fallback están implementados y son demostrables mediante simulación de
timeout o desconexión.

### Integrante 3: seguridad, sesión, validación e interfaz

**Archivos:** `autenticacion.py`, `main.py`, `.env.example`, `.gitignore`, `CodigoUML1/app.py` y `requirements.txt`.

#### Credenciales y control de versiones

`main.py` llama a `load_dotenv()` mediante `python-dotenv`. `Autenticacion`
obtiene usuarios y hashes desde `os.environ` y verifica credenciales mediante
PBKDF2-SHA256 con salt e iteraciones configurables por la clase. No se guardan
contraseñas planas; el valor de `.env` contiene hashes con el formato
`pbkdf2_sha256$iteraciones$salt$digest`.

`.env.example` es una plantilla distribuible con nombres (`API_URL`,
`API_TIMEOUT`, `DB_PATH`, `AUTH_USERNAME`, `AUTH_PASSWORD_HASH`,
`EMPLOYEE_USERNAME`, `EMPLOYEE_PASSWORD_HASH`) y sin secretos reales.
`.gitignore` excluye `.env`, bases SQLite, entornos virtuales, cachés y logs;
la excepción `!.env.example` permite conservar la plantilla.

#### Sesión y control de flujo

La aplicación inicializa `st.session_state["autenticado"]` y
`st.session_state["rol"]` con `setdefault`. Si no existe una sesión válida,
`mostrar_login()` renderiza el formulario y `st.stop()` impide que se ejecute
el CRUD.

El control requerido por la rúbrica debe expresarse así, antes de renderizar módulos protegidos:

```python
st.session_state.setdefault("autenticado", False)
st.session_state.setdefault("rol", None)

if not st.session_state["autenticado"]:
    mostrar_login()
    st.stop()

if st.session_state["rol"] != "Administrador":
    ocultar_o_bloquear_modulos_administrativos()
```

Después de verificar las credenciales, `st.session_state["autenticado"] = True`
permite continuar; `rol` restringe módulos sensibles. Administradores ven los
seis módulos y empleados solo los módulos operativos. Al cerrar sesión, ambos
valores vuelven a `False`/`None`.

#### Validación, sanitización y UX

Los constructores y setters eliminan espacios con `strip()`, rechazan nombres vacíos, validan correo, exigen longitud mínima de contraseña, impiden salarios negativos y exigen horas mayores que cero. Los formularios convierten explícitamente `int()` y `float()` y capturan `ValueError`; los valores ausentes o de tipo inesperado pueden producir `TypeError`, que debe capturarse junto con `ValueError` en validadores de entrada para impedir que un formulario rompa la aplicación.

Streamlit refuerza esas reglas con `number_input(min_value=0)`, rangos de horas, fechas coherentes, botones deshabilitados cuando las listas están vacías y mensajes `st.error`, `st.warning` y `st.info`. Los textos ingresados deben conservarse como datos parametrizados, nunca interpolarse en SQL. La eliminación exige checkbox de confirmación y las pantallas muestran `ID - Nombre` para evitar seleccionar registros ambiguos.

---

## 3. Pauta de exposición, evidencia y decisiones de diseño

### 3.1 Secuencia recomendada

1. Presentar el problema: centralizar personas, proyectos, horas e indicadores.
2. Mostrar el mapa UML-Python: `Usuario`, `Empleado`, `Administrador`, listas de asociación, composición y tabla puente.
3. Ejecutar un alta, una consulta, una actualización y una eliminación confirmada.
4. Provocar un duplicado para evidenciar `sqlite3.IntegrityError` y mostrar `PRAGMA foreign_keys = ON`.
5. Desconectar la API o simular timeout; explicar `raise_for_status()`, las cuatro excepciones y el fallback SQLite.
6. Mostrar `.env.example` y `.gitignore` sin revelar `.env`; explicar PBKDF2-SHA256, salt y la diferencia entre hash y cifrado.
7. Mostrar el login Streamlit, el filtro por rol, el botón Cerrar sesión y las métricas de Open-Meteo con su fallback.

### 3.2 Evidencia técnica por integrante

**Integrante 1:** `class Empleado(Usuario)`, `self.__salario`, `@property`, `@salario.setter`, `proyecto_empleados`, `sqlite3.connect()`, `PRAGMA`, CRUD parametrizado, commits/rollbacks y FKs.

**Integrante 2:** `requests.get(..., timeout=5)`, `raise_for_status()`, `serie[0]["valor"]`, validación de tipos, fallback SQLite, valores iniciales y adaptador Open-Meteo.

**Integrante 3:** `load_dotenv()`, `os.environ`, PBKDF2-SHA256, `.env.example`, `.gitignore`, `st.session_state["autenticado"]`, roles, `st.stop()` y control de confirmación.

### 3.3 Argumentación del uso de IA

La IA se usó como apoyo para detectar operaciones faltantes, proponer separación de responsabilidades y revisar escenarios de error. Cada sugerencia se contrastó con el UML, el código y el comportamiento esperado:

- Una propuesta de CRUD concentrado en `main.py` mezclaba presentación, dominio y persistencia; se modificó para mantener repositorio, modelos e interfaz separados.
- Las listas en memoria no sobrevivían al reinicio; se refactorizó la relación persistente con `proyecto_empleados`.
- La lectura directa de `response.json()` podía tratar como válida una respuesta 4xx/5xx; se añadió `raise_for_status()` antes de procesarla.
- Capturar solo una excepción genérica ocultaba el diagnóstico; se separaron `Timeout`, `ConnectionError`, `HTTPError`/`RequestException` y errores de validación.
- Devolver `None` dejaba paneles vacíos; se incorporó SQLite y valores predeterminados para indicadores económicos.
- Se detectaron riesgos de secretos en código, acciones destructivas y listas vacías; se aplicaron `.env`, `.gitignore`, confirmación y estados deshabilitados.

La decisión final siempre fue aceptar, modificar o rechazar la propuesta después de comprobar seguridad, mantenibilidad, integridad referencial y continuidad operativa.

---

## 4. Matriz de evaluación de IA vinculada a los 22 criterios

La siguiente matriz reproduce los 22 criterios de `rubrica.txt` y vincula cada uno con evidencia concreta del proyecto. Las etiquetas `G` e `I` se conservan exactamente como aparecen en la pauta. La columna de estado distingue una explicación documentada de una funcionalidad que todavía requiere cambios en el código.

| Nº | Criterio / evidencia | Código exacto de `rubrica.txt` | Falla detectada por revisión | Refactorización o decisión | Estado |
|---:|---|---|---|---|---|
| 1 | Clases, atributos, constructores, métodos y relaciones UML | `[2.1.1.G.1]` | CRUD y dominio inicialmente mezclados | Modelos, constructores, métodos, asociaciones, herencia y tabla puente | Implementado |
| 2 | Correspondencia verbal UML-Python | `[2.1.1.I.2]` | La correspondencia podía quedar implícita | Se explican `class Empleado(Usuario)`, propiedades, listas, FKs y `JOIN` | Documentado |
| 3 | Encapsulamiento, abstracción y reutilización | `[2.1.2.G.3]` | Atributos públicos permitían estados inválidos y duplicación | ABC `Usuario`, `super()`, atributos privados y reglas en el dominio | Implementado |
| 4 | Justificación del encapsulamiento y arquitectura | `[2.1.2.I.4]` | Validar solo en UI y repetir lógica reducía seguridad | `@property`, setters, separación por capas y reutilización heredada | Documentado |
| 5 | Conexión oficial y CRUD funcional | `[2.1.3.G.5]` | Persistencia inicial incompleta | `sqlite3`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`, FKs y confirmación | Implementado |
| 6 | Parámetros de conexión y lógica CRUD | `[2.1.3.I.6]` | Conexiones y operaciones no estaban justificadas | `sqlite3.connect()`, `PRAGMA`, context managers, `?`, `fetchone()` y `fetchall()` | Documentado |
| 7 | `try-except`, errores de BD y entradas | `[2.1.4.G.7]` | Duplicados y datos inválidos podían interrumpir el flujo | `IntegrityError`, `sqlite3.Error`, validadores y mensajes Streamlit | Parcial: reforzar `OperationalError` explícito |
| 8 | Explicación de excepciones y validaciones | `[2.1.4.I.8]` | Capturas genéricas ocultaban causas | Se explican fallas de PK/UNIQUE/FK, `ValueError`, `TypeError` y sanitización | Documentado |
| 9 | Análisis y prueba de código generado por IA | `[2.1.5.G.9]` | Propuestas iniciales mezclaban capas o carecían de fallback | Pruebas de duplicados, API caída, JSON inválido y listas vacías; luego se refactorizó | Documentado |
| 10 | Transparencia y evaluación crítica de IA | `[2.1.5.I.10]` | Adoptar sugerencias sin revisión podía introducir riesgos | Se identifican fragmentos apoyados, riesgos de seguridad, eficiencia y coherencia | Documentado |
| 11 | Solicitudes HTTP y JSON | `[3.1.1.G.11]` | API lenta o respuesta no JSON podía romper el flujo | `requests.get()`, `timeout=5`, `response.json()` y validación de diccionario | Implementado |
| 12 | Extracción e integración de datos API | `[3.1.1.G.12]` | Acceso directo a claves podía producir errores | `serie[0]["valor"]`, fecha, `ValidadorIndicadores` y persistencia SQLite | Implementado |
| 13 | Explicación de HTTP, JSON e integración | `[3.1.1.I.13]` | El contrato externo no estaba descrito paso a paso | Se documentan endpoint, parámetros, JSON, normalización y flujo hasta la UI | Documentado |
| 14 | Autenticación, credenciales y saneamiento | `[3.1.2.G.14]` | La primera versión comparaba credenciales sin hash resistente | `Autenticacion.generar_hash()` y `verificar_hash()` con PBKDF2-SHA256, salt e iteraciones | Implementado / Excelente |
| 15 | Información sensible y control de sesión/API | `[3.1.2.G.15]` | La primera versión no restringía módulos web | `.env`, `.gitignore`, login Streamlit, `st.session_state`, roles, `st.stop()` y Cerrar sesión | Implementado / Excelente |
| 16 | Fundamentación de autenticación, saneamiento y sesión | `[3.1.2.I.16]` | Consola y Streamlit requerían una distinción explícita | Se explica PBKDF2, login web, roles y guard de sesión con evidencia ejecutable | Documentado / Excelente |
| 17 | Excepciones de ejecución, red y timeout | `[3.1.3.G.17]` | Capturar solo errores generales ocultaba diagnóstico | `requests.Timeout`, `ConnectionError`, `RequestException` y validaciones | Implementado |
| 18 | Códigos HTTP, continuidad y errores seguros | `[3.1.3.G.18]` | JSON se procesaba antes de validar HTTP | `raise_for_status()`, diferenciación 200/4xx/5xx, clima Open-Meteo y fallback SQLite | Implementado / Excelente |
| 19 | Fundamentación de errores HTTP y continuidad | `[3.1.3.I.19]` | La resiliencia no estaba argumentada operacionalmente | Se explica jerarquía de excepciones, timeout, fallback y comunicación al usuario | Documentado |
| 20 | Evidencia del uso de IA | `[3.1.4.G.20]` | El origen de las propuestas podía quedar ambiguo | Se documentan sugerencias de IA, pruebas realizadas y decisiones finales | Documentado |
| 21 | Vulnerabilidades, redundancias y refactorización | `[3.1.4.G.21]` | SQL concatenado, secretos, listas volátiles y paneles vacíos | Parámetros `?`, `.env`, tabla puente, timeout, fallback y separación de capas | Documentado |
| 22 | Fundamentación completa del uso de IA | `[3.1.4.I.22]` | Faltaba vincular análisis, riesgos y decisiones | La sección 3.3 y esta matriz explican adoptar, modificar o descartar código | Documentado |

### 4.1 Síntesis de cumplimiento

La matriz demuestra detección de tres categorías de problemas: **seguridad**, como secretos en código, SQL concatenado y comparación ingenua; **redundancia o baja mantenibilidad**, como CRUD concentrado, validación duplicada y listas no persistentes; y **fallas de disponibilidad**, como ausencia de timeout, procesamiento de estados HTTP erróneos y paneles vacíos ante caída de red. La refactorización aplicada prioriza encapsulamiento, consultas parametrizadas, transacciones, validación, manejo específico de excepciones y fallback.

Los criterios de seguridad, sesión web y resiliencia externa quedan implementados y verificables: PBKDF2-SHA256 con salt, login con roles y `st.stop()`, Open-Meteo con `timeout=5`, manejo explícito de errores y fallback SQLite. Las conexiones SQLite se mantienen por operación y se cierran con gestores de contexto, por lo que no se requiere compartir una conexión ni usar `check_same_thread=False`.

### 4.2 Cierre oral

EcoTech no solo ejecuta el caso feliz: valida entradas, protege consultas, controla integridad, identifica errores HTTP y de red, conserva indicadores locales y comunica al usuario cuándo opera en modo degradado. La IA aceleró la exploración y la refactorización, pero la solución final se decidió mediante revisión humana del UML, del código real, de la seguridad y de la evidencia exigida por la rúbrica.
