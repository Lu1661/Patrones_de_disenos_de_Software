# CONTROLADOR DEL CATALOGO DE PRODUCTOS IMPORTADOS.

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
    # DEVUELVE EL CATALOGO CORPORATIVO DE PRODUCTOS.

    servicio = obtener_servicio("productos")
    return respuesta_exitosa(servicio.listar(), "Productos consultados.")


@productos_bp.post("")
def registrar_producto():
    # REGISTRA UN PRODUCTO IMPORTADO JUNTO CON SU STOCK INICIAL.

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
    # ACTUALIZA LA INFORMACION CORPORATIVA DE UN PRODUCTO.

    servicio = obtener_servicio("productos")
    producto = servicio.actualizar(id_producto, obtener_datos_solicitud())
    return respuesta_exitosa(producto, "Producto actualizado correctamente.")


@productos_bp.delete("/<int:id_producto>")
@requiere_administrador
def eliminar_producto(id_producto: int):
    # DESACTIVA UN PRODUCTO SIN BORRAR INVENTARIOS NI VENTAS.

    servicio = obtener_servicio("productos")
    producto = servicio.desactivar(id_producto)
    return respuesta_exitosa(producto, "Producto eliminado correctamente.")

