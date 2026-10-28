# CONTROLADOR DE LA PANTALLA INICIAL.

from flask import Blueprint, render_template


inicio_bp = Blueprint("inicio", __name__)


@inicio_bp.get("/")
def mostrar_inicio() -> str:
    # MUESTRA EL ESTADO INICIAL DEL PROYECTO SERF.

    # ============================================================
    # BLOQUE: PANTALLA INICIAL
    # Este bloque confirma que Flask reconoce la estructura del
    # proyecto antes de incorporar los modulos del negocio.
    # ============================================================
    return render_template("inicio.html")

