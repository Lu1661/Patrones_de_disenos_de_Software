# CONTROLADOR DE LA PANTALLA INICIAL.

from flask import Blueprint, abort, redirect, render_template, url_for


inicio_bp = Blueprint("inicio", __name__)


MODULOS_DISPONIBLES = {
    "resumen",
    "configuracion",
    "productos",
    "inventario",
    "ventas",
    "reportes",
}


@inicio_bp.get("/")
def mostrar_inicio():
    # ENVIA LA ENTRADA PRINCIPAL AL RESUMEN DEL SISTEMA.

    return redirect(url_for("inicio.mostrar_modulo", modulo="resumen"))


@inicio_bp.get("/<modulo>")
def mostrar_modulo(modulo: str) -> str:
    # MUESTRA EL MODULO INDICADO Y CONSERVA SU RUTA EN EL NAVEGADOR.

    # ============================================================
    # BLOQUE: PANTALLA INICIAL
    # Este bloque confirma que Flask reconoce la estructura del
    # proyecto antes de incorporar los modulos del negocio.
    # ============================================================
    if modulo not in MODULOS_DISPONIBLES:
        abort(404)

    return render_template("inicio.html", seccion_inicial=modulo)

