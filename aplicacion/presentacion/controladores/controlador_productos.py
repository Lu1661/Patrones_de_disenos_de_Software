"""Controlador del catalogo de productos importados."""

from flask import Blueprint

from aplicacion.dependencias import obtener_servicio
from aplicacion.presentacion.controladores.controlador_autenticacion import (
    requiere_administrador,
)
from aplicacion.presentacion.respuestas import (
    obtener_datos_solicitud,
    respuesta_exitosa,
)


productos_bp = Blueprint("productos", __name__, url_prefix="/api/productos")


@productos_bp.get("")
def listar_productos():
    """Retorna el catalogo corporativo de productos."""

    servicio = obtener_servicio("productos")
    return respuesta_exitosa(servicio.listar(), "Productos consultados.")


@productos_bp.post("")
def registrar_producto():
    """Registra un producto importado junto con su stock inicial."""

    servicio = obtener_servicio("productos")
    producto, inventario = servicio.registrar_con_stock(
        obtener_datos_solicitud()
    )
    return respuesta_exitosa(
        {"producto": producto, "inventario": inventario},
        "Producto e inventario registrados correctamente.",
        201,
    )


@productos_bp.put("/<int:id_producto>")
@requiere_administrador
def actualizar_producto(id_producto: int):
    """Actualiza la informacion corporativa de un producto."""

    servicio = obtener_servicio("productos")
    producto = servicio.actualizar(id_producto, obtener_datos_solicitud())
    return respuesta_exitosa(producto, "Producto actualizado correctamente.")


@productos_bp.delete("/<int:id_producto>")
@requiere_administrador
def eliminar_producto(id_producto: int):
    """Desactiva un producto sin borrar inventarios ni ventas."""

    servicio = obtener_servicio("productos")
    producto = servicio.desactivar(id_producto)
    return respuesta_exitosa(producto, "Producto eliminado correctamente.")

