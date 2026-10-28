# CREACION Y CONFIGURACION INICIAL DE LA APLICACION FLASK.

from pathlib import Path

from flask import Flask, jsonify, redirect, request, session, url_for
from mysql.connector import Error as ErrorMySQL
from mysql.connector import IntegrityError

from aplicacion.configuracion.configuracion_entorno import ConfiguracionEntorno
from aplicacion.dependencias import configurar_dependencias
from aplicacion.presentacion.controladores.controlador_autenticacion import (
    autenticacion_bp,
)
from aplicacion.presentacion.controladores.controlador_configuracion import (
    configuracion_bp,
)
from aplicacion.presentacion.controladores.controlador_inventario import inventario_bp
from aplicacion.presentacion.controladores.controlador_inicio import inicio_bp
from aplicacion.presentacion.controladores.controlador_productos import productos_bp
from aplicacion.presentacion.controladores.controlador_reportes import reportes_bp
from aplicacion.presentacion.controladores.controlador_ventas import ventas_bp


def crear_aplicacion() -> Flask:
    # CREA LA INSTANCIA FLASK Y REGISTRA SUS COMPONENTES INICIALES.

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
    configurar_dependencias(aplicacion)

    aplicacion.register_blueprint(autenticacion_bp)
    aplicacion.register_blueprint(inicio_bp)
    aplicacion.register_blueprint(configuracion_bp)
    aplicacion.register_blueprint(productos_bp)
    aplicacion.register_blueprint(inventario_bp)
    aplicacion.register_blueprint(ventas_bp)
    aplicacion.register_blueprint(reportes_bp)

    # ============================================================
    # BLOQUE: PROTECCION GENERAL DE PANTALLAS Y API
    # Este bloque exige una sesion administrativa para usar el sistema.
    # Las peticiones de la API reciben JSON y las pantallas van al login.
    # ============================================================
    @aplicacion.before_request
    def comprobar_sesion_administrativa():
        rutas_libres = {"autenticacion.login", "static"}

        if request.endpoint in rutas_libres or session.get("usuario_admin"):
            return None

        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "exito": False,
                        "mensaje": "Debes iniciar sesión para continuar.",
                    }
                ),
                401,
            )

        return redirect(url_for("autenticacion.login"))

    # ============================================================
    # BLOQUE: ENCABEZADOS DE SEGURIDAD DEL NAVEGADOR
    # Este bloque limita la carga de recursos externos, el uso en marcos
    # y el almacenamiento local de las pantallas financieras protegidas.
    # ============================================================
    @aplicacion.after_request
    def agregar_encabezados_seguridad(respuesta):
        respuesta.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Referrer-Policy"] = "no-referrer"
        respuesta.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        if request.endpoint != "static":
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    # ============================================================
    # BLOQUE: MANEJO UNIFORME DE ERRORES DEL BACKEND
    # Este bloque evita mostrar detalles internos de MySQL y entrega al
    # frontend mensajes sencillos junto con el codigo HTTP apropiado.
    # ============================================================
    @aplicacion.errorhandler(ValueError)
    def manejar_validacion(error: ValueError):
        return jsonify({"exito": False, "mensaje": str(error)}), 400

    @aplicacion.errorhandler(IntegrityError)
    def manejar_conflicto(_error: IntegrityError):
        return (
            jsonify(
                {
                    "exito": False,
                    "mensaje": "El registro ya existe o esta siendo utilizado.",
                }
            ),
            409,
        )

    @aplicacion.errorhandler(ErrorMySQL)
    def manejar_error_mysql(_error: ErrorMySQL):
        return (
            jsonify(
                {
                    "exito": False,
                    "mensaje": "No fue posible completar la operacion en MySQL.",
                }
            ),
            500,
        )

    @aplicacion.errorhandler(RuntimeError)
    def manejar_configuracion(error: RuntimeError):
        return jsonify({"exito": False, "mensaje": str(error)}), 503

    return aplicacion

