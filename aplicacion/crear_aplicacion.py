"""Creacion y configuracion inicial de la aplicacion Flask."""

from pathlib import Path

from flask import Flask

from aplicacion.configuracion.configuracion_entorno import ConfiguracionEntorno
from aplicacion.presentacion.controladores.controlador_inicio import inicio_bp


def crear_aplicacion() -> Flask:
    """Crea la instancia Flask y registra sus componentes iniciales."""

    ruta_aplicacion = Path(__file__).resolve().parent

    # ============================================================
    # BLOQUE: CREACION DE LA APLICACION FLASK
    # Este bloque establece las carpetas de plantillas y recursos
    # para mantener separada la presentacion del resto del sistema.
    # ============================================================
    aplicacion = Flask(
        __name__,
        template_folder=str(ruta_aplicacion / "presentacion" / "plantillas"),
        static_folder=str(ruta_aplicacion / "presentacion" / "recursos"),
        static_url_path="/recursos",
    )
    aplicacion.config.from_object(ConfiguracionEntorno)
    aplicacion.register_blueprint(inicio_bp)

    return aplicacion

