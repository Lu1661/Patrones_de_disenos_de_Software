"""Controlador de existencias por filial."""

from flask import Blueprint, request

from aplicacion.dependencias import obtener_servicio
from aplicacion.presentacion.respuestas import (
    obtener_datos_solicitud,
    respuesta_exitosa,
)
from aplicacion.servicios.utilidades import convertir_entero


inventario_bp = Blueprint("inventario", __name__, url_prefix="/api/inventario")


@inventario_bp.get("/catalogo")
def listar_inventario_catalogo():
    """Retorna los precios locales que complementan el catalogo."""

    servicio = obtener_servicio("inventario")
    inventario = servicio.listar_todos()
    return respuesta_exitosa(inventario, "Precios de venta consultados.")


@inventario_bp.get("")
def listar_inventario():
    """Retorna las existencias de la filial indicada."""

    id_filial = convertir_entero(request.args.get("id_filial"), "id_filial")
    servicio = obtener_servicio("inventario")
    inventario = servicio.listar_por_filial(id_filial)
    return respuesta_exitosa(inventario, "Inventario consultado.")


@inventario_bp.post("/reponer")
def reponer_inventario():
    """Incrementa el stock de un producto ya asignado a una filial."""

    servicio = obtener_servicio("inventario")
    inventario = servicio.reponer(obtener_datos_solicitud())
    return respuesta_exitosa(inventario, "Stock repuesto correctamente.")

