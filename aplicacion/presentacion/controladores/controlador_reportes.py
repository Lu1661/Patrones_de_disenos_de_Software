# CONTROLADOR DE GENERACION DE REPORTES FINANCIEROS.

from flask import Blueprint

from aplicacion.dependencias import obtener_servicio
from aplicacion.presentacion.respuestas import (
    obtener_datos_solicitud,
    respuesta_exitosa,
)


reportes_bp = Blueprint("reportes", __name__, url_prefix="/api/reportes")


@reportes_bp.post("/generar")
def generar_reporte():
    # GENERA UN REPORTE POR PERIODO Y FILIAL PARA LA VISTA IMPRIMIBLE.

    servicio = obtener_servicio("reportes")
    reporte = servicio.generar(obtener_datos_solicitud())
    return respuesta_exitosa(reporte, "Reporte generado correctamente.")

