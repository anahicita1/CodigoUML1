from modelos.empleado import Empleado

class Departamento:
    def __init__(self, id_depto: int, nombre: str, gerente: str = "Por asignar"):
        self.__id_depto = id_depto
        self.__nombre = nombre
        self.__gerente = gerente
        self.__empleados = []

    @property
    def id_depto(self) -> int:
        return self.__id_depto

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def gerente(self) -> str:
        return self.__gerente

    @gerente.setter
    def gerente(self, nuevo_gerente: str):
        self.__gerente = nuevo_gerente

    # --- Métodos exigidos en el UML ---
    def agregar_empleado(self, emp: Empleado) -> bool:
        if emp not in self.__empleados:
            self.__empleados.append(emp)
            emp.asignar_departamento(self)
            return True
        return False

    def eliminar_empleado(self, emp: Empleado) -> bool:
        if emp in self.__empleados:
            self.__empleados.remove(emp)
            print(f"Empleado {emp.nombre} removido del departamento '{self.__nombre}'.")
            return True
        return False

    def obtener_empleados(self) -> list:
        return list(self.__empleados)
