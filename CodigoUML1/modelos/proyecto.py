class Proyecto:
    def __init__(self, id_proyecto: int, nombre: str, descripcion: str, fecha_inicio: str,
                 presupuesto: float = 0.0, fecha_fin_estimada: str = "", fecha_fin_real: str = ""):
        self.__id_proyecto = id_proyecto
        self.__nombre = nombre
        self.__descripcion = descripcion
        self.__fecha_inicio = fecha_inicio
        self.__fecha_fin_estimada = fecha_fin_estimada
        self.__fecha_fin_real = fecha_fin_real
        # "presupuesto" no está en el UML validado: extensión útil, a justificar en la defensa.
        self.__presupuesto = presupuesto
        self.__empleados = []

    @property
    def id_proyecto(self) -> int:
        return self.__id_proyecto

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def descripcion(self) -> str:
        return self.__descripcion

    @property
    def fecha_inicio(self) -> str:
        return self.__fecha_inicio

    @property
    def fecha_fin_estimada(self) -> str:
        return self.__fecha_fin_estimada

    @property
    def fecha_fin_real(self) -> str:
        return self.__fecha_fin_real

    @property
    def presupuesto(self) -> float:
        return self.__presupuesto

    # --- Métodos exigidos en el UML ---
    def asignar_empleado(self, emp) -> bool:
        if emp not in self.__empleados:
            self.__empleados.append(emp)
            emp.asignar_proyecto(self)  # mantiene la asociación bidireccional consistente
            print(f"Empleado {emp.nombre} asignado al proyecto '{self.__nombre}'.")
            return True
        return False

    def desasignar_empleado(self, emp) -> bool:
        if emp in self.__empleados:
            self.__empleados.remove(emp)
            emp.desasignar_proyecto(self)
            print(f"Empleado {emp.nombre} desasignado del proyecto '{self.__nombre}'.")
            return True
        return False

    def obtener_empleados(self) -> list:
        return list(self.__empleados)
