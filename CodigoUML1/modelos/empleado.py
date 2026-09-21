from modelos.usuario import Usuario
from modelos.registro_tiempo import RegistroTiempo


class Empleado(Usuario):
    def __init__(self, id_usuario: int, nombre: str, correo: str, contrasena_cifrada: str,
                 direccion: str, telefono: str, fecha_contrato: str, salario: float, cargo: str = "Empleado"):
        super().__init__(id_usuario, nombre, correo, contrasena_cifrada)

        if salario < 0:
            raise ValueError("El salario no puede ser un valor negativo.")

        self.__direccion = direccion
        self.__telefono = telefono
        self.__fecha_contrato = fecha_contrato
        self.__salario = salario
        # "cargo" no está en el UML validado: se mantiene como extensión útil
        # para el negocio, pero debe poder justificarse en la defensa.
        self.__cargo = cargo

        self.__departamento = None       # Asociación con Departamento (antes solo se imprimía)
        self.__proyectos = []            # Asociación 0..* -- 0..* con Proyecto
        self.__registros_tiempo = []     # Composición UML: Empleado 1 -- 0..* RegistroTiempo

    # --- Getters y Setters ---
    @property
    def direccion(self) -> str:
        return self.__direccion

    @property
    def telefono(self) -> str:
        return self.__telefono

    @property
    def fecha_contrato(self) -> str:
        return self.__fecha_contrato

    @property
    def salario(self) -> float:
        return self.__salario

    @salario.setter
    def salario(self, nuevo_salario: float):
        if nuevo_salario < 0:
            raise ValueError("El salario no puede ser negativo.")
        self.__salario = nuevo_salario

    @property
    def cargo(self) -> str:
        return self.__cargo

    @property
    def departamento(self):
        return self.__departamento

    # --- Métodos exigidos en el UML ---
    def registrar_horas(self, fecha: str, horas: int, proy) -> None:
        """Ahora crea y guarda un RegistroTiempo real (composición), no solo imprime."""
        id_registro_local = len(self.__registros_tiempo) + 1
        registro = RegistroTiempo(
            id_registro=id_registro_local,
            id_usuario=self.id_usuario,
            fecha=fecha,
            horas=horas,
            descripcion=f"Horas trabajadas en el proyecto '{proy.nombre}'",
        )
        self.__registros_tiempo.append(registro)
        registro.validar_horas()
        print(f"Empleado {self.nombre} registró {horas} hrs el {fecha} en el proyecto '{proy.nombre}'.")

    def obtener_registros_tiempo(self) -> list:
        return list(self.__registros_tiempo)

    def obtener_salario(self) -> float:
        return self.__salario

    def asignar_departamento(self, depto) -> None:
        """Ahora sí guarda la referencia; antes solo imprimía un mensaje."""
        self.__departamento = depto
        print(f"Empleado {self.nombre} asignado al departamento '{depto.nombre}'.")

    def asignar_proyecto(self, proy) -> None:
        if proy not in self.__proyectos:
            self.__proyectos.append(proy)

    def desasignar_proyecto(self, proy) -> None:
        if proy in self.__proyectos:
            self.__proyectos.remove(proy)

    def obtener_proyectos(self) -> list:
        return list(self.__proyectos)

    # --- Métodos Abstractos Implementados ---
    def iniciar_sesion(self) -> bool:
        print(f"Empleado {self.nombre} ha iniciado sesión exitosamente.")
        return True

    def cerrar_sesion(self) -> None:
        print(f"Empleado {self.nombre} cerró sesión.")
