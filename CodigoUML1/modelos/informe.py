class Informe:
    def __init__(self, id_informe: int, tipo: str, contenido: str, fecha_generacion: str = "2026-09-10", formato_exportacion: str = "PDF"):
        self.__id_informe = id_informe
        self.__tipo = tipo
        self.__contenido = contenido
        self.__fecha_generacion = fecha_generacion
        self.__formato_exportacion = formato_exportacion

    @property
    def id_informe(self) -> int:
        return self.__id_informe

    @property
    def tipo(self) -> str:
        return self.__tipo

    @property
    def contenido(self) -> str:
        return self.__contenido

    @property
    def fecha_generacion(self) -> str:
        return self.__fecha_generacion

    @property
    def formato_exportacion(self) -> str:
        return self.__formato_exportacion

    # --- Métodos exigidos en el UML ---
    def exportar_pdf(self) -> None:
        print(f"Informe #{self.__id_informe} ('{self.__tipo}') exportado exitosamente a formato PDF.")

    def exportar_excel(self) -> None:
        print(f"Informe #{self.__id_informe} ('{self.__tipo}') exportado exitosamente a formato EXCEL.")
