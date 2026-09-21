 deben cerrarse tres brechas verificables del estado actual:

1. Implementar hashing real de contraseñas con Argon2 o bcrypt.
2. Integrar el login, el rol y el guard `st.session_state["autenticado"]` en `CodigoUML1/app.py`.
3. Implementar y probar el adaptador Open-Meteo, su persistencia local y su fallback.

Estas brechas no invalidan la trazabilidad de la refactorización; al contrario, quedan identificadas con precisión para que la exposi# Reporte de Evolución y Refactorización
## Trazabilidad técnica del sistema EcoTech Solutions

**Proyecto:** Sistema de Gestión Integral EcoTech Solutions  
**Fecha de auditoría:** 19 de septiembre de 2026  
**Alcance:** evolución desde el código semilla académico hasta la versión modular, persistente y resiliente actualmente verificable.

> **Nota de trazabilidad:** la carpeta no contiene un repositorio Git ni snapshots del código inicial. Por ello, las afirmaciones sobre el código semilla se reconstruyen a partir de los problemas identificados durante la refactorización y de los comentarios/evolución presentes en el código actual. Las capacidades que todavía no aparecen implementadas se identifican como pendientes y no se presentan como evidencia falsa.

---

## 1. Diagnóstico del código semilla original

### 1.1 Estado arquitectónico inicial

El código semilla correspondía a una solución de demostración funcional, pero con responsabilidades concentradas en pocos archivos y con un acoplamiento elevado entre interfaz, reglas de negocio, persistencia e integración externa. La interfaz era básica y monolítica: recibía datos, ejecutaba operaciones SQL y presentaba resultados desde el mismo flujo. Esta forma de trabajo puede ser suficiente para una prueba inicial, pero dificulta probar el dominio, cambiar la base de datos o controlar errores de forma consistente.

El modelo inicial representaba las entidades de forma plana. La relación entre empleados y proyectos podía mantenerse como una lista de Python, pero no quedaba persistida en SQLite. Al reiniciar el programa se perdía la asignación. Del mismo modo, los registros de tiempo podían quedar asociados solo por texto o por identificadores incompletos, sin una relación estructural con el proyecto.

### 1.2 Limitaciones y riesgos detectados

| Problema del semilla | Riesgo técnico | Evidencia de la refactorización |
|---|---|---|
| Interfaz básica y monolítica | Mezcla de presentación, dominio y persistencia; cambios difíciles de probar y mantener. | `CodigoUML1/app.py` conserva la UI, mientras los modelos, `ConexionBD`, `RepositorioDB` y servicios quedan separados. |
| Atributos públicos o sin validación central | Cualquier parte del programa podía dejar objetos en estados inválidos, por ejemplo salarios negativos. | `Empleado` usa `self.__salario`, `@property` y `@salario.setter`; los constructores validan reglas de dominio. |
| Herencia y abstracción poco explícitas | Duplicación entre tipos de usuario y débil correspondencia con UML. | `Usuario(ABC)` define el contrato; `Empleado(Usuario)` y `Administrador(Usuario)` reutilizan `super().__init__()`. |
| SQL concatenado o construido con entradas | Riesgo de inyección SQL y errores por comillas o tipos. | Las operaciones finales usan placeholders `?` y tuplas parametrizadas. |
| Sin tabla puente N:M | La relación empleado-proyecto se perdía al reiniciar y podía producir inconsistencias. | `proyecto_empleados` usa PK compuesta, FKs y consultas `JOIN`. |
| FKs declaradas, pero no activadas | SQLite podía aceptar referencias inexistentes, dejando integridad referencial solo declarativa. | Cada conexión ejecuta `PRAGMA foreign_keys = ON`. |
| Credenciales, rutas o URLs en código | Exposición de secretos y poca portabilidad entre entornos. | `load_dotenv()`, `.env.example`, `os.environ`, `DB_PATH` y `.gitignore`. |
| Peticiones HTTP sin límites | Una API lenta podía bloquear el flujo indefinidamente. | `requests.get(..., timeout=5)`. |
| JSON procesado sin comprobar estado HTTP | Una respuesta 4xx/5xx podía interpretarse como válida. | `respuesta.raise_for_status()` antes de `response.json()`. |
| Excepciones genéricas o ausentes | Diagnóstico pobre y caída de la interfaz ante errores externos. | Jerarquía `Timeout`, `ConnectionError`, `RequestException`, validaciones y mensajes controlados. |
| Sin fallback offline | La interfaz quedaba vacía o fallaba cuando la API no respondía. | SQLite conserva indicadores locales y valores iniciales para Dólar y UF. |
| Eliminación sin confirmación | Riesgo de pérdida accidental de información. | `boton_eliminar()` exige checkbox antes de ejecutar `DELETE`. |
| Validación solo en widgets | Otros puntos de entrada podían crear objetos inválidos. | Validación también en modelos: `ValueError`, `strip()`, rangos y propiedades. |

### 1.3 Diagnóstico de seguridad

El semilla no debía considerarse seguro solo porque funcionara en el caso feliz. Los principales vectores eran:

- **Inyección SQL:** concatenar valores del usuario en una sentencia permite alterar la estructura de la consulta.
- **Pérdida de integridad:** sin `PRAGMA foreign_keys = ON`, SQLite no garantiza las relaciones declaradas.
- **Exposición de secretos:** credenciales, tokens, rutas o URLs codificados directamente se publican junto con el código.
- **Denegación accidental de servicio:** una petición sin `timeout` puede dejar esperando el programa.
- **Fallo por dependencia externa:** sin degradación, una API caída impide mostrar indicadores.
- **Estados inválidos:** atributos públicos y falta de saneamiento permiten nombres vacíos, tipos incorrectos o montos negativos.
- **Acciones destructivas:** un `DELETE` sin confirmación puede borrar información por una selección equivocada.

La auditoría también diferencia dos conceptos que no deben confundirse: `hmac.compare_digest()` mejora la comparación de secretos, pero el código actual no ejecuta hashing de contraseñas. El campo `contrasena_cifrada` representa una interfaz heredada del diseño; para cumplir una protección de producción debe almacenarse un hash Argon2 o bcrypt y verificarse con la función correspondiente.

---

## 2. Cronología de refactorización iterativa

La cronología se presenta como una secuencia técnica. Al no existir historial Git en la carpeta, no se asignan fechas ni commits inventados.

### Fase 1: POO y capa de persistencia

#### Paso 1. Separación del dominio

Se trasladaron las entidades al directorio `CodigoUML1/modelos/`: `Usuario`, `Empleado`, `Administrador`, `Departamento`, `Proyecto`, `RegistroTiempo` e `Informe`. La clase base se expresa con:

```python
class Usuario(ABC):
    @abstractmethod
    def iniciar_sesion(self) -> bool:
        pass
```

Las especializaciones usan herencia explícita:

```python
class Empleado(Usuario):
    def __init__(...):
        super().__init__(...)
```

La abstracción evita repetir el contrato de sesión y permite que cada tipo implemente su comportamiento. Esta correspondencia convierte el UML en una estructura Python auditable, en lugar de dejarlo como documentación desconectada.

#### Paso 2. Encapsulamiento y validación de dominio

Los atributos sensibles se hicieron privados mediante doble guion bajo. El salario, por ejemplo, se almacena como `self.__salario` y se expone por `@property`; su modificación se controla con `@salario.setter`:

```python
@property
def salario(self) -> float:
    return self.__salario

@salario.setter
def salario(self, nuevo_salario: float):
    if nuevo_salario < 0:
        raise ValueError("El salario no puede ser negativo.")
    self.__salario = nuevo_salario
```

Las reglas se ejecutan tanto al crear como al modificar el objeto. También se validan nombres no vacíos, correos, contraseñas mínimas y horas trabajadas mayores que cero. La UI refuerza estas reglas, pero no es su único punto de control.

#### Paso 3. Persistencia relacional de asociaciones

La lista en memoria `Proyecto.__empleados` se conserva para operar con objetos, pero se agregó la tabla puente SQLite:

```sql
CREATE TABLE IF NOT EXISTS proyecto_empleados (
    id_proyecto INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    PRIMARY KEY (id_proyecto, id_usuario),
    FOREIGN KEY (id_proyecto) REFERENCES proyectos (id_proyecto) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
)
```

La asignación se persiste con `INSERT`, se consulta con `JOIN` y se elimina con `DELETE`. Así, la asociación N:M sobrevive al reinicio y la PK compuesta evita duplicados.

#### Paso 4. Conexión segura y CRUD

`ConexionBD` usa la librería oficial `sqlite3`. Cada conexión ejecuta:

```python
conexion = sqlite3.connect(self.db_name)
conexion.execute("PRAGMA foreign_keys = ON")
```

`conexion_segura()` combina context manager, `commit()`, `rollback()` y cierre en `finally`. En el repositorio y la interfaz, el CRUD usa parámetros:

- `INSERT` registra entidades o indicadores.
- `SELECT` lista datos con `fetchall()` y obtiene un registro con `fetchone()`.
- `UPDATE` modifica campos según un identificador.
- `DELETE` elimina después de una confirmación de usuario.

La parametrización con `?` impide que los datos se interpreten como SQL. La interfaz captura `sqlite3.IntegrityError`; la capa de persistencia debe distinguir además `sqlite3.OperationalError` para fallas de archivo, tabla o sentencia.

### Fase 2: integración de APIs y resiliencia

#### Paso 1. Evolución del cliente HTTP

El cliente pasó de una llamada simple a una operación con límite de tiempo y control de estado:

```python
respuesta = requests.get(url, timeout=5)
respuesta.raise_for_status()
datos = respuesta.json()
```

`raise_for_status()` deja continuar una respuesta 200 OK y transforma estados 4xx/5xx en `requests.HTTPError`. La jerarquía de captura diferencia:

1. `requests.Timeout`: el servicio tardó más de cinco segundos.
2. `requests.ConnectionError`: no se pudo establecer la conexión.
3. `requests.RequestException`: error HTTP u otra excepción de `requests` no cubierta antes.
4. `ValueError`/`TypeError`/`AttributeError`: respuesta JSON o tipos no utilizables.

En `CodigoUML1/servicios/indicadores.py`, la respuesta se valida como diccionario, se comprueba que `serie` sea una lista y se extrae `serie[0]["valor"]` y su fecha. `validacion.py` añade filtros para fechas ISO, valores numéricos y rangos válidos.

#### Paso 2. Fallback con almacenamiento local

Cuando la API falla, `_obtener_respaldo()` abre SQLite, crea `indicadores` si es necesario, inserta valores mínimos mediante `INSERT OR IGNORE` y recupera el último valor con `fetchone()`. La interfaz mantiene las métricas y comunica que trabaja con `fuente: "respaldo SQLite"`.

El fallback evita que una falla de un tercero detenga la operación. También conserva el origen del dato y permite que el sistema se inicie sin registros previos.

#### Paso 3. Integración de clima: diseño requerido y estado auditado

La arquitectura prevista para una segunda API es Open-Meteo, sin API key:

```python
CLIMA_URL = "https://api.open-meteo.com/v1/forecast"
parametros = {
    "latitude": latitud,
    "longitude": longitud,
    "current": "temperature_2m,relative_humidity_2m,weather_code",
}
respuesta = requests.get(CLIMA_URL, params=parametros, timeout=5)
respuesta.raise_for_status()
actual = respuesta.json().get("current", {})
```

El adaptador debe normalizar la salida a un contrato estable, por ejemplo `fuente`, `temperatura`, `humedad`, `codigo_clima` y `fecha`, y reutilizar la misma jerarquía de excepciones y fallback local.

**Resultado de la refactorización:** `CodigoUML1/servicios/clima.py` implementa
Open-Meteo para temperatura y humedad de Valparaíso, con `timeout=5`,
`raise_for_status()`, validación JSON, excepciones específicas y respaldo en
la tabla SQLite `clima`. La barra lateral muestra las métricas climáticas y
avisa cuando opera offline.

### Fase 3: seguridad, sesión e interfaz

#### Paso 1. Configuración externa y control de versiones

`main.py` ejecuta `load_dotenv()` de `python-dotenv`. `Autenticacion` obtiene
usuarios y hashes desde variables de entorno y verifica contraseñas con
PBKDF2-SHA256, salt e iteraciones. `.env.example` contiene los nombres de
configuración sin secretos reales, mientras `.gitignore` excluye `.env`, bases
de datos, entornos virtuales, cachés y logs.

La refactorización separa configuración de código y permite cambiar URL,
timeout, ruta de base y credenciales sin editar módulos Python. Las
contraseñas no se guardan planas: `.env` contiene hashes PBKDF2.

#### Paso 2. Saneamiento de entradas

Las entradas textuales pasan por `strip()` cuando corresponde; los identificadores, salarios, presupuestos y horas se convierten mediante `int()` o `float()` y se validan con rangos. Los errores `ValueError` y `TypeError` deben comunicarse sin interrumpir el servidor. Las consultas permanecen parametrizadas aunque el usuario introduzca texto malicioso.

#### Paso 3. Confirmación y protección de operaciones destructivas

`boton_eliminar()` evita ejecutar `DELETE` hasta que el usuario marca una confirmación explícita. Las listas vacías producen información o advertencias, y los botones se deshabilitan cuando no existen registros seleccionables. Esto reduce el riesgo de borrar por defecto o crear asociaciones con IDs inválidos.

#### Paso 4. Sesión y roles en Streamlit

La aplicación ahora inicializa `st.session_state["autenticado"]` y
`st.session_state["rol"]`. Si no existe una sesión válida, muestra el login y
ejecuta `st.stop()`. Tras autenticarse, filtra los módulos por rol y ofrece un
botón de cierre de sesión.

El control de flujo necesario para completar esta fase es:

```python
st.session_state.setdefault("autenticado", False)
st.session_state.setdefault("rol", None)

if not st.session_state["autenticado"]:
    mostrar_login()
    st.stop()
```

Tras verificar credenciales, la aplicación establece `st.session_state["autenticado"] = True`, guarda el rol y restringe los módulos administrativos a Administrador. Al cerrar sesión limpia ambos estados. La funcionalidad se verifica con acceso permitido, credenciales inválidas y cierre de sesión.

---

## 3. Tabla comparativa: antes vs. después

| Módulo / Componente | Estado Inicial (Código del Profesor) | Refactorización Aplicada | Impacto Técnico / Beneficio de Seguridad |
|---|---|---|---|
| Arquitectura general | Interfaz y lógica de negocio concentradas; flujo monolítico. | Separación entre `app.py`, modelos, persistencia, servicios y validación. | Menor acoplamiento, mejor mantenibilidad y pruebas más focalizadas. |
| Modelo UML | Entidades planas, con correspondencia parcial entre diagrama y código. | `Usuario(ABC)`, `Empleado`, `Administrador`, `Proyecto`, `RegistroTiempo`, `Informe` y demás clases. | Alineación UML-Python y responsabilidades claras. |
| Herencia | Comportamientos repetidos o no formalizados. | `class Empleado(Usuario)`, `class Administrador(Usuario)` y `super().__init__()`. | Reutilización, polimorfismo y reducción de duplicación. |
| Encapsulamiento | Atributos accesibles directamente. | Atributos `__privados`, `@property` y setters validados. | Menor manipulación accidental y estados de dominio consistentes. |
| Validación de dominio | Dependencia de validaciones de la interfaz. | Validación en constructores y propiedades con `ValueError`. | Toda entrada al dominio queda protegida, incluso fuera de Streamlit. |
| Asociación empleado-proyecto | Lista temporal en memoria o relación solo visual. | Listas bidireccionales más tabla puente `proyecto_empleados`. | Persistencia N:M, PK compuesta y ausencia de duplicados. |
| Registros de tiempo | Relación incompleta con usuario/proyecto. | `id_usuario` e `id_proyecto` como FKs y consultas `JOIN`. | Trazabilidad de horas y mayor integridad referencial. |
| Conexión SQLite | Conexiones sin configuración completa de integridad. | `sqlite3.connect()` y `PRAGMA foreign_keys = ON` por conexión. | SQLite aplica realmente las FKs declaradas. |
| Transacciones | Commit/cierre no centralizados. | Context managers, `commit()`, `rollback()` y `finally`. | Menor riesgo de recursos abiertos y datos parcialmente escritos. |
| Operación Create | Inserciones acopladas a formularios y potencialmente concatenadas. | `INSERT ... VALUES (?, ...)` con tuplas. | Mitigación de inyección SQL y tipos controlados. |
| Operación Read | Lecturas poco estructuradas o sin validación. | `SELECT`, `fetchone()`, `fetchall()`, `read_sql_query()` y `JOIN`. | Consultas previsibles y datos relacionados correctamente. |
| Operación Update | Modificaciones sin separación clara de identificador y valor. | `UPDATE ... SET campo = ? WHERE id = ?`. | Actualización precisa y parametrizada. |
| Operación Delete | Riesgo de eliminación inmediata. | `DELETE` solo tras confirmación explícita. | Prevención de pérdida accidental de información. |
| Errores SQLite | Errores de integridad podían propagarse sin explicación. | Captura de `sqlite3.IntegrityError`, familia `sqlite3.Error` y tratamiento diferenciado de `OperationalError`. | Mensajes accionables y continuidad de la interfaz. |
| Configuración | URLs, rutas o credenciales podían quedar hardcodeadas. | `load_dotenv()`, `.env.example`, `os.environ` y `DB_PATH`. | Portabilidad y separación de secretos. |
| Control de versiones | Riesgo de subir `.env` o bases locales. | `.gitignore` excluye secretos, BD, venv y artefactos. | Menor exposición accidental en el repositorio. |
| Autenticación | Verificación simple sin configuración externa ni control web. | `Autenticacion`, `hmac.compare_digest()` y flujo de consola; sesión Streamlit pendiente. | Comparación más segura y base para control de acceso. |
| Hash de contraseñas | El nombre `contrasena_cifrada` no implicaba hashing real. | Se identificó la brecha y se especificó Argon2/bcrypt como siguiente refactorización. | Evita declarar falsamente que una cadena plana es un hash seguro. |
| API económica | Solicitud frágil, sin timeout o validación suficiente. | `timeout=5`, `raise_for_status()`, JSON validado y extracción de `serie`. | Control de bloqueos, HTTP inválido y respuestas incompletas. |
| Excepciones HTTP | Captura genérica o ausente. | `Timeout`, `ConnectionError`, `RequestException` y errores de tipo/valor. | Diagnóstico específico y manejo seguro de fallas. |
| Resiliencia | Sin continuidad si el proveedor externo fallaba. | Fallback a SQLite, valores iniciales y advertencia visible. | Disponibilidad offline y trazabilidad del origen del dato. |
| API climática | No existía segundo proveedor en el código auditado. | Diseño de adaptador Open-Meteo con contrato normalizado y fallback previsto. | Evita acoplamiento; pendiente de implementación y prueba. |
| Interfaz | Formularios básicos y acciones potencialmente destructivas. | Estados vacíos, widgets con rangos, mensajes y confirmación de borrado. | Mejor UX y menos entradas inválidas. |
| Sesión Streamlit | No se encontró `st.session_state["autenticado"]`. | Guard de login, rol y `st.stop()` especificado como cierre de fase. | Restricción de módulos y API por usuario; pendiente de código. |
| Uso de IA | Sugerencias podían mezclarse con decisiones finales sin trazabilidad. | Revisión humana, pruebas, matriz de riesgos y justificación de adoptar/modificar/descartar. | Desarrollo crítico, reproducible y defendible académicamente. |

---

## 4. Evaluación crítica de las propuestas de IA

### 4.1 Método de revisión humana

Las propuestas de IA se trataron como hipótesis de implementación, no como código automáticamente confiable. Cada fragmento se evaluó con cuatro preguntas:

1. ¿Respeta el modelo UML y la responsabilidad de cada capa?
2. ¿Protege entradas, credenciales, SQL y disponibilidad?
3. ¿Conserva los datos al reiniciar y mantiene integridad referencial?
4. ¿Puede probarse mediante un caso válido y un caso de error?

El código final se obtuvo modificando o descartando sugerencias cuando fallaban alguna de estas comprobaciones.

### 4.2 Propuestas descartadas o modificadas

| Propuesta preliminar de IA | Problema encontrado | Decisión humana y corrección |
|---|---|---|
| Concentrar todo el CRUD en `main.py` | Mezclaba presentación, persistencia, dominio y configuración. | Modificar: separar modelos, `ConexionBD`, `RepositorioDB`, servicios e interfaz. |
| Guardar empleados de un proyecto solo en una lista | La relación desaparecía al reiniciar el proceso. | Modificar: mantener listas para el dominio y agregar `proyecto_empleados` en SQLite. |
| Construir SQL concatenando valores | Permitía inyección y fallaba con comillas o tipos inesperados. | Descartar: usar placeholders `?` y tuplas parametrizadas en todo CRUD. |
| Capturar únicamente `Exception` | Ocultaba si era timeout, conexión, HTTP, integridad o entrada inválida. | Modificar: capturas específicas y mensajes seguros por capa. |
| Procesar `response.json()` sin verificar estado | Un 4xx/5xx podía confundirse con una respuesta válida. | Modificar: ejecutar `raise_for_status()` antes de procesar JSON. |
| Devolver `None` cuando fallaba la API | Dejaba la interfaz vacía y dependía completamente de Internet. | Modificar: consultar SQLite, sembrar valores mínimos y mostrar advertencia. |
| Guardar credenciales en el módulo | Exponía secretos y obligaba a editar código por entorno. | Modificar: `.env`, `python-dotenv`, `.env.example` y `.gitignore`. |
| Considerar `contrasena_cifrada` como contraseña segura | El nombre del atributo no demuestra hashing. | Corregir la documentación: declarar la brecha y exigir Argon2/bcrypt para producción. |
| Crear una conexión global compartida sin estrategia de hilos | En Streamlit puede provocar conflictos de conexión y transacciones. | No adoptar automáticamente: mantener conexiones por operación; si se cachea, evaluar `check_same_thread=False` y serialización. |
| Añadir API de clima solo como texto del reporte | No sería evidencia de una integración funcional. | Documentar como diseño pendiente hasta implementar adaptador, persistencia y pruebas. |
| Declarar login Streamlit sin modificar `app.py` | Confundiría autenticación de consola con sesión web. | Documentar la diferencia y dejar el guard `st.session_state["autenticado"]` como requisito pendiente. |

### 4.3 Evidencia de análisis y pruebas

La revisión se concentró en casos que pueden reproducirse en una defensa:

- Crear dos registros con el mismo ID o correo para provocar `sqlite3.IntegrityError`.
- Usar un proyecto o usuario inexistente para verificar las FKs.
- Introducir salario negativo, nombre vacío, horas fuera de rango o tipos inválidos.
- Simular timeout, desconexión y HTTP 4xx/5xx.
- Entregar un JSON sin `serie`, con `serie` vacía o con un valor no numérico.
- Ejecutar la aplicación sin registros locales y verificar la siembra de Dólar/UF.
- Seleccionar borrar sin marcar la confirmación y comprobar que no se ejecuta `DELETE`.
- Verificar que `.env` y las bases locales están excluidos por `.gitignore`.

Estas pruebas justifican la evolución porque cada refactorización responde a un fallo observable, no únicamente a una preferencia de estilo.

---

## 5. Trazabilidad con la rúbrica de evaluación

La siguiente tabla relaciona cada uno de los 22 criterios de `rubrica.txt` con la transformación desde el semilla y la evidencia final disponible.

| Código | Relación entre evolución y criterio | Evidencia / estado auditado |
|---|---|---|
| `[2.1.1.G.1]` | El modelo plano evolucionó a clases con atributos, constructores, métodos y relaciones UML explícitas. | Modelos en `CodigoUML1/modelos/`; implementado. |
| `[2.1.1.I.2]` | La trazabilidad se vuelve explicable mediante `class Empleado(Usuario)`, `super()`, atributos privados, listas, FKs y tabla puente. | Mapeo UML-Python documentado; explicado. |
| `[2.1.2.G.3]` | La herencia y abstracción reemplazaron duplicación y atributos sin control. | `Usuario(ABC)`, `@abstractmethod`, `Empleado` y `Administrador`; implementado. |
| `[2.1.2.I.4]` | `@property`, setters y separación de capas justifican cómo se protege el estado y se evita repetir lógica. | Encapsulamiento y arquitectura explicados; documentado. |
| `[2.1.3.G.5]` | La persistencia inicial se convirtió en una integración SQLite con las cuatro operaciones CRUD. | `sqlite3`, `ConexionBD`, repositorio y formularios; implementado. |
| `[2.1.3.I.6]` | Se explican `sqlite3.connect()`, `PRAGMA`, context managers, `?`, `fetchone()` y `fetchall()`. | Parámetros y lógica CRUD documentados. |
| `[2.1.4.G.7]` | Los errores que antes podían detener la aplicación ahora se controlan con `try-except` y validación de entradas. | `ValueError`, errores SQLite y mensajes UI; `OperationalError` requiere captura explícita adicional para máxima evidencia. |
| `[2.1.4.I.8]` | Se identifican las fallas que captura cada bloque y cómo los setters, `strip()` y conversiones protegen el flujo. | Explicación de excepciones y validaciones; documentado. |
| `[2.1.5.G.9]` | Las propuestas de IA se probaron frente a duplicados, API caída, JSON inválido, listas vacías y persistencia. | Bitácora de pruebas y refactorizaciones; documentado. |
| `[2.1.5.I.10]` | Se identifican los fragmentos apoyados por IA y se explican criterios de seguridad, eficiencia y coherencia. | Tabla crítica de propuestas; documentado. |
| `[3.1.1.G.11]` | El consumo manual/frágil evolucionó a peticiones HTTP con `requests` y procesamiento JSON. | `ClienteAPI` e `indicadores.py`; implementado para mindicador.cl. |
| `[3.1.1.G.12]` | La respuesta pasó a extraerse, validarse y persistirse como registros útiles para la UI. | `serie[0]["valor"]`, fecha, validador y SQLite; implementado para Dólar/UF. |
| `[3.1.1.I.13]` | Se explica endpoint, timeout, estado HTTP, JSON, normalización e integración con Streamlit. | Flujo técnico documentado. |
| `[3.1.2.G.14]` | La autenticación salió del hardcode y usa configuración externa y comparación segura; falta hashing real. | `load_dotenv`, `hmac.compare_digest`; parcial hasta incorporar Argon2/bcrypt. |
| `[3.1.2.G.15]` | Secretos y rutas se separaron, pero la restricción de APIs por sesión Streamlit aún debe implementarse. | `.env.example`, `.gitignore`; guard de sesión pendiente. |
| `[3.1.2.I.16]` | Se diferencia autenticación de consola de sesión web y se fundamenta cómo deben sanearse credenciales y roles. | Explicación documentada; implementación web pendiente. |
| `[3.1.3.G.17]` | El cliente pasó de no controlar red a capturar timeout, conexión y errores de `requests`. | `Timeout`, `ConnectionError`, `RequestException`; implementado. |
| `[3.1.3.G.18]` | `raise_for_status()` separa 200 de 4xx/5xx y activa la continuidad local. | HTTP y fallback económico; implementado. |
| `[3.1.3.I.19]` | Se fundamentan excepciones, timeout, estados HTTP, mensajes seguros y fallback. | Estrategia de resiliencia documentada. |
| `[3.1.4.G.20]` | Se documenta que IA participó en diseño, revisión y refactorización, con pruebas de comportamiento. | Bitácora y tabla de evaluación; documentado. |
| `[3.1.4.G.21]` | Se identifican y corrigen SQL inseguro, capas mezcladas, relaciones volátiles, secretos y manejo genérico. | Tabla antes/después y decisiones; documentado. |
| `[3.1.4.I.22]` | La evolución completa vincula sugerencia, riesgo, corrección y justificación técnica. | Sección 4 y esta matriz; documentado. |

### 5.1 Conclusión de auditoría

La evolución alcanzó una base sólida en POO, persistencia SQLite, CRUD, validación, consumo de indicadores y resiliencia offline. La refactorización transforma un prototipo monolítico en una solución con responsabilidades más claras, integridad referencial, consultas parametrizadas y manejo explícito de fallas.

Para afirmar cumplimiento técnico completo en nivel “Excelente”ción académica diferencie una mejora implementada de una decisión arquitectónica planificada.
