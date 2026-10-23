"""Controlador de la pantalla inicial."""

from flask import Blueprint, render_template


inicio_bp = Blueprint("inicio", __name__)


@inicio_bp.get("/")
def mostrar_inicio() -> str:
    """Muestra el estado inicial del proyecto SERF."""

    # ============================================================
    # BLOQUE: PANTALLA INICIAL
    # Este bloque confirma que Flask reconoce la estructura del
    # proyecto antes de incorporar los modulos del negocio.
    # ============================================================
    return render_template("inicio.html")

