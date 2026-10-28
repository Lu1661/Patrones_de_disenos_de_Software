# CONTROLADOR DE FILIALES Y TIPOS DE CAMBIO.

from flask import Blueprint

from aplicacion.dependencias import obtener_servicio
from aplicacion.presentacion.controladores.controlador_autenticacion import (
    requiere_administrador,
)
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
    # DEVUELVE LAS FILIALES DISPONIBLES PARA LOS FORMULARIOS.

    servicio = obtener_servicio("filiales")
    return respuesta_exitosa(servicio.listar(), "Filiales consultadas.")


@configuracion_bp.post("/filiales")
def registrar_filial():
    # REGISTRA UNA SEDE COMERCIAL CON SU MONEDA LOCAL.

    servicio = obtener_servicio("filiales")
    filial = servicio.registrar(obtener_datos_solicitud())
    return respuesta_exitosa(filial, "Filial registrada correctamente.", 201)


@configuracion_bp.put("/filiales/<int:id_filial>")
@requiere_administrador
def actualizar_filial(id_filial: int):
    # ACTUALIZA UNA SEDE MEDIANTE UNA OPERACION ADMINISTRATIVA.

    servicio = obtener_servicio("filiales")
    filial = servicio.actualizar(id_filial, obtener_datos_solicitud())
    return respuesta_exitosa(filial, "Filial actualizada correctamente.")


@configuracion_bp.delete("/filiales/<int:id_filial>")
@requiere_administrador
def eliminar_filial(id_filial: int):
    # DESACTIVA UNA SEDE Y GUARDA SU HISTORIAL.

    servicio = obtener_servicio("filiales")
    filial = servicio.desactivar(id_filial)
    return respuesta_exitosa(filial, "Filial eliminada correctamente.")


@configuracion_bp.get("/tipos-cambio")
def listar_tipos_cambio():
    # DEVUELVE EL HISTORIAL DE TASAS HACIA EUR.

    servicio = obtener_servicio("tipos_cambio")
    return respuesta_exitosa(servicio.listar(), "Tipos de cambio consultados.")


@configuracion_bp.post("/tipos-cambio")
def registrar_tipo_cambio():
    # REGISTRA UNA NUEVA TASA VIGENTE HACIA EUR.

    servicio = obtener_servicio("tipos_cambio")
    tasa = servicio.registrar(obtener_datos_solicitud())
    return respuesta_exitosa(tasa, "Tipo de cambio registrado correctamente.", 201)


@configuracion_bp.put("/tipos-cambio/<int:id_tipo_cambio>")
@requiere_administrador
def actualizar_tipo_cambio(id_tipo_cambio: int):
    # ACTUALIZA UNA TASA EXISTENTE MEDIANTE UNA OPERACION ADMINISTRATIVA.

    servicio = obtener_servicio("tipos_cambio")
    tasa = servicio.actualizar(id_tipo_cambio, obtener_datos_solicitud())
    return respuesta_exitosa(tasa, "Tipo de cambio actualizado correctamente.")


@configuracion_bp.delete("/tipos-cambio/<int:id_tipo_cambio>")
@requiere_administrador
def eliminar_tipo_cambio(id_tipo_cambio: int):
    # DESACTIVA UNA TASA Y GUARDA SU REGISTRO HISTORICO.

    servicio = obtener_servicio("tipos_cambio")
    tasa = servicio.desactivar(id_tipo_cambio)
    return respuesta_exitosa(tasa, "Tipo de cambio eliminado correctamente.")

