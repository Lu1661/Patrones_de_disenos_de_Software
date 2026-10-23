"""Respuestas comunes utilizadas por los controladores Flask."""

from flask import jsonify, request

from aplicacion.presentacion.serializadores import serializar


def obtener_datos_solicitud() -> dict:
    """Acepta JSON y conserva compatibilidad con formularios HTML."""

    datos_json = request.get_json(silent=True)
    if isinstance(datos_json, dict):
        return datos_json
    return request.form.to_dict()


def respuesta_exitosa(datos, mensaje: str, estado: int = 200):
    """Mantiene una estructura uniforme en las respuestas correctas."""

    return (
        jsonify(
            {
                "exito": True,
                "mensaje": mensaje,
                "datos": serializar(datos),
            }
        ),
        estado,
    )
