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

    def actualizar(self, id_filial: int, datos: dict) -> Filial:
        """Actualiza una filial existente sin alterar sus operaciones."""

        actual = self._repositorio.obtener_por_id(id_filial)
        if actual is None:
            raise ValueError("La filial indicada no existe.")
        filial = Filial(
            codigo=str(obtener_requerido(datos, "codigo")),
            nombre=str(obtener_requerido(datos, "nombre")),
            pais=str(obtener_requerido(datos, "pais")),
            ciudad=str(obtener_requerido(datos, "ciudad")),
            codigo_divisa=str(obtener_requerido(datos, "codigo_divisa")),
            activa=actual.activa,
            id_filial=id_filial,
        )
        self._repositorio.actualizar(filial)
        return filial

    def desactivar(self, id_filial: int) -> Filial:
        """Desactiva una filial y conserva inventarios y ventas historicas."""

        filial = self._repositorio.obtener_por_id(id_filial)
        if filial is None or not filial.activa:
            raise ValueError("La filial indicada no existe o ya esta inactiva.")
        self._repositorio.desactivar(id_filial)
        filial.activa = False
        return filial
