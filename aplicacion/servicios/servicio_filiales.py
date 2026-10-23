"""Procesos de registro y consulta de filiales."""

from aplicacion.dominio.entidades.filial import Filial
from aplicacion.persistencia.repositorios.repositorio_filiales import (
    RepositorioFiliales,
)
from aplicacion.servicios.utilidades import obtener_requerido


class ServicioFiliales:
    """Coordina las reglas sencillas de las sedes comerciales."""

    def __init__(self, repositorio: RepositorioFiliales) -> None:
        self._repositorio = repositorio

    def listar(self) -> list[Filial]:
        """Retorna todas las filiales registradas."""

        return self._repositorio.listar()

    def registrar(self, datos: dict) -> Filial:
        """Valida y registra una nueva filial."""

        filial = Filial(
            codigo=str(obtener_requerido(datos, "codigo")),
            nombre=str(obtener_requerido(datos, "nombre")),
            pais=str(obtener_requerido(datos, "pais")),
            ciudad=str(obtener_requerido(datos, "ciudad")),
            codigo_divisa=str(obtener_requerido(datos, "codigo_divisa")),
        )
        self._repositorio.crear(filial)
        return filial
