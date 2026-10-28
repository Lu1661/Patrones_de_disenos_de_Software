# CONTROLADOR DE REGISTRO Y CONSULTA DE VENTAS.

from datetime import date

from flask import Blueprint, request

from aplicacion.dependencias import obtener_servicio
from aplicacion.presentacion.respuestas import (
    obtener_datos_solicitud,
    respuesta_exitosa,
)
from aplicacion.servicios.utilidades import convertir_entero, convertir_fecha


ventas_bp = Blueprint("ventas", __name__, url_prefix="/api/ventas")


@ventas_bp.get("")
def listar_ventas():
    # CONSULTA VENTAS POR PERIODO Y, OPCIONALMENTE, POR FILIAL.

    hoy = date.today()
    fecha_inicio = convertir_fecha(
        request.args.get("fecha_inicio", hoy.replace(day=1).isoformat()),
        "fecha_inicio",
    )
    fecha_fin = convertir_fecha(
        request.args.get("fecha_fin", hoy.isoformat()),
        "fecha_fin",
    )
    id_filial_recibido = request.args.get("id_filial")
    id_filial = (
        convertir_entero(id_filial_recibido, "id_filial")
        if id_filial_recibido not in (None, "")
        else None
    )

    servicio = obtener_servicio("ventas")
    ventas = servicio.listar_por_periodo(fecha_inicio, fecha_fin, id_filial)
    return respuesta_exitosa(ventas, "Ventas consultadas.")


@ventas_bp.post("")
def registrar_venta():
    # REGISTRA EL COMPROBANTE Y DESCUENTA EL STOCK EN UNA SOLA OPERACION.

    servicio = obtener_servicio("ventas")
    venta = servicio.registrar(obtener_datos_solicitud())
    return respuesta_exitosa(venta, "Venta registrada correctamente.", 201)

