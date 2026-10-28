# CONTROLADOR DE EXISTENCIAS POR FILIAL.

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
    # DEVUELVE LOS PRECIOS LOCALES QUE COMPLEMENTAN EL CATALOGO.

    servicio = obtener_servicio("inventario")
    inventario = servicio.listar_todos()
    return respuesta_exitosa(inventario, "Precios de venta consultados.")


@inventario_bp.get("")
def listar_inventario():
    # DEVUELVE LAS EXISTENCIAS DE LA FILIAL INDICADA.

    id_filial = convertir_entero(request.args.get("id_filial"), "id_filial")
    servicio = obtener_servicio("inventario")
    inventario = servicio.listar_por_filial(id_filial)
    return respuesta_exitosa(inventario, "Inventario consultado.")


@inventario_bp.post("/reponer")
def reponer_inventario():
    # INCREMENTA EL STOCK DE UN PRODUCTO YA ASIGNADO A UNA FILIAL.

    servicio = obtener_servicio("inventario")
    inventario = servicio.reponer(obtener_datos_solicitud())
    return respuesta_exitosa(inventario, "Stock repuesto correctamente.")

