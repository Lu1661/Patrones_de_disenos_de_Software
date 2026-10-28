# PROCESOS DE REGISTRO Y CONSULTA DE FILIALES.

from aplicacion.dominio.entidades.filial import Filial
from aplicacion.persistencia.repositorios.repositorio_filiales import (
    RepositorioFiliales,
)
from aplicacion.servicios.utilidades import obtener_requerido


class ServicioFiliales:
    # COORDINA LAS REGLAS SENCILLAS DE LAS SEDES COMERCIALES.

    def __init__(self, repositorio: RepositorioFiliales) -> None:
        self._repositorio = repositorio

    def listar(self) -> list[Filial]:
        # DEVUELVE TODAS LAS FILIALES REGISTRADAS.

        return self._repositorio.listar()

    def registrar(self, datos: dict) -> Filial:
        # VALIDA Y REGISTRA UNA NUEVA FILIAL.

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
        # ACTUALIZA UNA FILIAL EXISTENTE SIN ALTERAR SUS OPERACIONES.

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
        # DESACTIVA UNA FILIAL Y GUARDA INVENTARIOS Y VENTAS HISTORICAS.

        filial = self._repositorio.obtener_por_id(id_filial)
        if filial is None or not filial.activa:
            raise ValueError("La filial indicada no existe o ya esta inactiva.")
        self._repositorio.desactivar(id_filial)
        filial.activa = False
        return filial
