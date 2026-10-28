# PROCESO DE CONSULTA Y ACTUALIZACION DEL INVENTARIO POR FILIAL.

from aplicacion.dominio.entidades.inventario_filial import InventarioFilial
from aplicacion.persistencia.repositorios.repositorio_inventario import (
    RepositorioInventario,
)
from aplicacion.servicios.utilidades import convertir_entero, obtener_requerido


class ServicioInventario:
    # EXPONE OPERACIONES SIMPLES SOBRE LAS EXISTENCIAS DE UNA FILIAL.

    def __init__(self, repositorio: RepositorioInventario) -> None:
        self._repositorio = repositorio

    def listar_por_filial(self, id_filial: int) -> list[InventarioFilial]:
        # DEVUELVE EL INVENTARIO CORRESPONDIENTE A UNA FILIAL.

        return self._repositorio.listar_por_filial(id_filial)

    def listar_todos(self) -> list[InventarioFilial]:
        # DEVUELVE LOS PRECIOS LOCALES PARA MOSTRARLOS EN EL CATALOGO.

        return self._repositorio.listar_todos()

    def reponer(self, datos: dict) -> InventarioFilial:
        # INCREMENTA EL STOCK Y DEVUELVE EL NUEVO ESTADO DEL INVENTARIO.

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

