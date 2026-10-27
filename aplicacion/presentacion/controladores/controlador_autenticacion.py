"""Controlador del acceso administrativo al sistema."""

from functools import wraps
from hmac import compare_digest

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


autenticacion_bp = Blueprint("autenticacion", __name__)


def requiere_administrador(funcion):
    """Permite ejecutar una operacion solamente a la cuenta administrativa."""

    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        # ============================================================
        # BLOQUE: AUTORIZACION DE OPERACIONES ADMINISTRATIVAS
        # Este bloque protege las modificaciones aunque alguien intente
        # llamar la API directamente sin utilizar los botones del sistema.
        # ============================================================
        if not session.get("usuario_admin"):
            return jsonify(
                {
                    "exito": False,
                    "mensaje": "Esta operacion requiere un usuario administrador.",
                }
            ), 403
        return funcion(*args, **kwargs)

    return funcion_protegida


@autenticacion_bp.route("/login", methods=["GET", "POST"])
def login():
    """Valida las credenciales administrativas antes de ingresar."""

    # ============================================================
    # BLOQUE: VALIDACION DEL ACCESO ADMINISTRATIVO
    # Este bloque compara los datos del formulario con la cuenta
    # configurada para el proyecto y crea la sesion del usuario.
    # ============================================================
    if session.get("usuario_admin"):
        return redirect(url_for("inicio.mostrar_inicio"))

    mensaje_error = None
    estado_http = 200

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        usuario_valido = compare_digest(usuario, current_app.config["ADMIN_USUARIO"])
        password_valido = compare_digest(
            password,
            current_app.config["ADMIN_PASSWORD"],
        )

        if usuario_valido and password_valido:
            session.clear()
            session["usuario_admin"] = usuario
            return redirect(url_for("inicio.mostrar_inicio"))

        mensaje_error = "Usuario o contraseña incorrectos."
        estado_http = 401

    return render_template("login.html", mensaje_error=mensaje_error), estado_http


@autenticacion_bp.post("/logout")
def logout():
    """Cierra la sesion administrativa y regresa al login."""

    # ============================================================
    # BLOQUE: CIERRE DE SESION
    # Este bloque elimina los datos de acceso guardados en Flask
    # para impedir que el navegador conserve una sesion anterior.
    # ============================================================
    session.clear()
    return redirect(url_for("autenticacion.login"))
