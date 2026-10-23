"""Controlador de filiales y tipos de cambio."""

from flask import Blueprint

from aplicacion.dependencias import obtener_servicio
from aplicacion.presentacion.respuestas import (
    obtener_datos_solicitud,
    respuesta_exitosa,
)


configuracion_bp = Blueprint(
    "configuracion",
    __name__,
    url_prefix="/api/configuracion",
)


@configuracion_bp.get("/filiales")
def listar_filiales():
    """Retorna las filiales disponibles para los formularios."""

    servicio = obtener_servicio("filiales")
    return respuesta_exitosa(servicio.listar(), "Filiales consultadas.")


@configuracion_bp.post("/filiales")
def registrar_filial():
    """Registra una sede comercial con su moneda local."""

    servicio = obtener_servicio("filiales")
    filial = servicio.registrar(obtener_datos_solicitud())
    return respuesta_exitosa(filial, "Filial registrada correctamente.", 201)


@configuracion_bp.get("/tipos-cambio")
def listar_tipos_cambio():
    """Retorna el historial de tasas hacia EUR."""

    servicio = obtener_servicio("tipos_cambio")
    return respuesta_exitosa(servicio.listar(), "Tipos de cambio consultados.")


@configuracion_bp.post("/tipos-cambio")
def registrar_tipo_cambio():
    """Registra una nueva tasa vigente hacia EUR."""

    servicio = obtener_servicio("tipos_cambio")
    tasa = servicio.registrar(obtener_datos_solicitud())
    return respuesta_exitosa(tasa, "Tipo de cambio registrado correctamente.", 201)

