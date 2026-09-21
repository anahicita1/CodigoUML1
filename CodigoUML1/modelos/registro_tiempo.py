class RegistroTiempo:
    def __init__(self, id_registro: int, id_usuario: int, fecha: str, horas: float,
                 descripcion: str = "Registro de trabajo", id_proyecto: int | None = None):
        if horas <= 0:
            raise ValueError("Las horas trabajadas deben ser mayores a cero.")
            
        self.__id_registro = id_registro
        self.__id_usuario = id_usuario
        self.__id_proyecto = id_proyecto
        self.__fecha = fecha
        self.__horas = horas
        self.__descripcion = descripcion

    @property
    def id_registro(self) -> int:
        return self.__id_registro

    @property
    def id_usuario(self) -> int:
        return self.__id_usuario

    @property
    def id_proyecto(self) -> int | None:
        return self.__id_proyecto

    @property
    def fecha(self) -> str:
        return self.__fecha

    @property
    def horas(self) -> float:
        return self.__horas

    @property
    def descripcion(self) -> str:
        return self.__descripcion

    # --- Método exigido en el UML ---
    def validar_horas(self) -> bool:
        if 0 < self.__horas <= 24:
            print(f"✅ Registro {self.__id_registro}: {self.__horas} hrs validadas correctamente.")
            return True
        print(f"Registro {self.__id_registro}: Horas fuera de rango permitido.")
        return False
