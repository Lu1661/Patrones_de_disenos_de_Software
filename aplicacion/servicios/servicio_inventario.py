"""Proceso de consulta y actualizacion del inventario por filial."""

from aplicacion.dominio.entidades.inventario_filial import InventarioFilial
from aplicacion.persistencia.repositorios.repositorio_inventario import (
    RepositorioInventario,
)
from aplicacion.servicios.utilidades import convertir_entero, obtener_requerido


class ServicioInventario:
    """Expone operaciones simples sobre las existencias de una filial."""

    def __init__(self, repositorio: RepositorioInventario) -> None:
        self._repositorio = repositorio

    def listar_por_filial(self, id_filial: int) -> list[InventarioFilial]:
        """Retorna el inventario correspondiente a una filial."""

        return self._repositorio.listar_por_filial(id_filial)

    def listar_todos(self) -> list[InventarioFilial]:
        """Retorna los precios locales para mostrarlos en el catalogo."""

        return self._repositorio.listar_todos()

    def reponer(self, datos: dict) -> InventarioFilial:
        """Incrementa el stock y retorna el nuevo estado del inventario."""

        id_filial = convertir_entero(
            obtener_requerido(datos, "id_filial"),
            "id_filial",
        )
        id_producto = convertir_entero(
            obtener_requerido(datos, "id_producto"),
            "id_producto",
        )
        cantidad = convertir_entero(
            obtener_requerido(datos, "cantidad"),
            "cantidad",
        )
        self._repositorio.reponer_stock(id_filial, id_producto, cantidad)
        inventario = self._repositorio.obtener(id_filial, id_producto)
        if inventario is None:
            raise ValueError("No fue posible recuperar el inventario actualizado.")
        return inventario

