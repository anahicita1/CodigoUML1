from modelos.usuario import Usuario
from modelos.empleado import Empleado
from modelos.informe import Informe


class Administrador(Usuario):
    def __init__(self, id_usuario: int, nombre: str, correo: str, contrasena_cifrada: str, nivel_acceso: int):
        super().__init__(id_usuario, nombre, correo, contrasena_cifrada)

        if nivel_acceso < 1:
            raise ValueError("El nivel de acceso debe ser un número entero positivo.")

        self.__nivel_acceso = nivel_acceso
        self.__informes = []  # Composición UML: Administrador 1 -- 0..* Informe

    @property
    def nivel_acceso(self) -> int:
        return self.__nivel_acceso

    def iniciar_sesion(self) -> bool:
        print(f"Administrador {self.nombre} (Nivel {self.__nivel_acceso}) ha iniciado sesión.")
        return True

    def cerrar_sesion(self) -> None:
        print(f"Administrador {self.nombre} ha cerrado sesión.")

    def registrar_nuevo_empleado(self, datos: Empleado) -> bool:
        """Método exigido por el UML (faltaba por completo en la versión anterior)."""
        if not isinstance(datos, Empleado):
            raise TypeError("Se esperaba una instancia de Empleado.")
        print(f"Administrador {self.nombre} registró al nuevo empleado '{datos.nombre}'.")
        return True

    def genera_reporte(self, tipo_informe: Informe) -> None:
        """Antes solo hacía print(); ahora sí materializa la composición con Informe."""
        if not isinstance(tipo_informe, Informe):
            raise TypeError("Se esperaba una instancia de Informe.")
        self.__informes.append(tipo_informe)
        print(f"Administrador {self.nombre} generó el informe: {tipo_informe.tipo}")

    def obtener_informes(self) -> list:
        return list(self.__informes)
