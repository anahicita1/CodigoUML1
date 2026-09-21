from abc import ABC, abstractmethod


class Usuario(ABC):
    """Clase base abstracta para todos los usuarios del sistema EcoTech."""

    def __init__(self, id_usuario: int, nombre: str, correo: str, contrasena_cifrada: str):
        self._id_usuario = id_usuario
        # Se asigna vía las properties (más abajo) para que TODAS las
        # validaciones se apliquen también en la construcción del objeto,
        # no solo si se modifican después.
        self.nombre = nombre
        self.correo = correo
        self.contrasena_cifrada = contrasena_cifrada

    @property
    def id_usuario(self) -> int:
        return self._id_usuario

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str):
        if not valor or not valor.strip():
            raise ValueError("El nombre no puede estar vacío.")
        self.__nombre = valor.strip()

    @property
    def correo(self) -> str:
        return self.__correo

    @correo.setter
    def correo(self, valor: str):
        if not valor or "@" not in valor:
            raise ValueError("El correo electrónico no tiene un formato válido.")
        self.__correo = valor

    @property
    def contrasena_cifrada(self) -> str:
        return self.__contrasena_cifrada

    @contrasena_cifrada.setter
    def contrasena_cifrada(self, nueva_contrasena: str):
        if not nueva_contrasena or len(nueva_contrasena) < 6:
            raise ValueError("La contraseña cifrada debe tener al menos 6 caracteres.")
        self.__contrasena_cifrada = nueva_contrasena

    @abstractmethod
    def iniciar_sesion(self) -> bool:
        pass

    @abstractmethod
    def cerrar_sesion(self) -> None:
        pass
