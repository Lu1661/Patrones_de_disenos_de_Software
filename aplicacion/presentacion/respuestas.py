# RESPUESTAS COMUNES UTILIZADAS POR LOS CONTROLADORES FLASK.

from flask import jsonify, request

from aplicacion.presentacion.serializadores import serializar


def obtener_datos_solicitud() -> dict:
    # ACEPTA JSON Y GUARDA COMPATIBILIDAD CON FORMULARIOS HTML.

    datos_json = request.get_json(silent=True)
    if isinstance(datos_json, dict):
        return datos_json
    return request.form.to_dict()


def respuesta_exitosa(datos, mensaje: str, estado: int = 200):
    # MANTIENE UNA ESTRUCTURA UNIFORME EN LAS RESPUESTAS CORRECTAS.

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
