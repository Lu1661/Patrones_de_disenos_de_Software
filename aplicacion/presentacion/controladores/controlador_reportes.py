"""Controlador de generacion de reportes financieros."""

from flask import Blueprint

from aplicacion.dependencias import obtener_servicio
from aplicacion.presentacion.respuestas import (
    obtener_datos_solicitud,
    respuesta_exitosa,
)


reportes_bp = Blueprint("reportes", __name__, url_prefix="/api/reportes")


@reportes_bp.post("/generar")
def generar_reporte():
    """Genera un reporte por periodo y filial para la vista imprimible."""

    servicio = obtener_servicio("reportes")
    reporte = servicio.generar(obtener_datos_solicitud())
    return respuesta_exitosa(reporte, "Reporte generado correctamente.")

