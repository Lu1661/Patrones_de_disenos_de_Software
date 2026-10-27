"""Controlador de filiales y tipos de cambio."""

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
    """Retorna las filiales disponibles para los formularios."""

    servicio = obtener_servicio("filiales")
    return respuesta_exitosa(servicio.listar(), "Filiales consultadas.")


@configuracion_bp.post("/filiales")
def registrar_filial():
    """Registra una sede comercial con su moneda local."""

    servicio = obtener_servicio("filiales")
    filial = servicio.registrar(obtener_datos_solicitud())
    return respuesta_exitosa(filial, "Filial registrada correctamente.", 201)


@configuracion_bp.put("/filiales/<int:id_filial>")
@requiere_administrador
def actualizar_filial(id_filial: int):
    """Actualiza una sede mediante una operacion administrativa."""

    servicio = obtener_servicio("filiales")
    filial = servicio.actualizar(id_filial, obtener_datos_solicitud())
    return respuesta_exitosa(filial, "Filial actualizada correctamente.")


@configuracion_bp.delete("/filiales/<int:id_filial>")
@requiere_administrador
def eliminar_filial(id_filial: int):
    """Desactiva una sede y conserva su historial."""

    servicio = obtener_servicio("filiales")
    filial = servicio.desactivar(id_filial)
    return respuesta_exitosa(filial, "Filial eliminada correctamente.")


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


@configuracion_bp.put("/tipos-cambio/<int:id_tipo_cambio>")
@requiere_administrador
def actualizar_tipo_cambio(id_tipo_cambio: int):
    """Actualiza una tasa existente mediante una operacion administrativa."""

    servicio = obtener_servicio("tipos_cambio")
    tasa = servicio.actualizar(id_tipo_cambio, obtener_datos_solicitud())
    return respuesta_exitosa(tasa, "Tipo de cambio actualizado correctamente.")


@configuracion_bp.delete("/tipos-cambio/<int:id_tipo_cambio>")
@requiere_administrador
def eliminar_tipo_cambio(id_tipo_cambio: int):
    """Desactiva una tasa y conserva su registro historico."""

    servicio = obtener_servicio("tipos_cambio")
    tasa = servicio.desactivar(id_tipo_cambio)
    return respuesta_exitosa(tasa, "Tipo de cambio eliminado correctamente.")

