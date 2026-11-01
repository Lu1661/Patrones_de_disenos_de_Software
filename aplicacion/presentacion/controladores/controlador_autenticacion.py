# CONTROLADOR DEL ACCESO ADMINISTRATIVO AL SISTEMA.

from functools import wraps
from hmac import compare_digest
from threading import Lock
from time import time

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
intentos_acceso = {}
bloqueo_intentos = Lock()


def clave_intento(usuario: str) -> str:
    # IDENTIFICA LOS INTENTOS POR USUARIO Y DIRECCION DE CONEXION.

    return f"{request.remote_addr or 'desconocida'}:{usuario.lower()}"


def acceso_bloqueado(clave: str) -> bool:
    # REVISA SI LA ESPERA TEMPORAL TODAVIA SIGUE ACTIVA.

    ahora = time()
    with bloqueo_intentos:
        registro = intentos_acceso.get(clave)
        if not registro:
            return False
        if registro["bloqueado_hasta"] > ahora:
            return True
        if registro["bloqueado_hasta"]:
            intentos_acceso.pop(clave, None)
    return False


def registrar_fallo(clave: str) -> bool:
    # CUENTA TRES FALLOS Y ACTIVA UNA PAUSA TEMPORAL.

    ahora = time()
    with bloqueo_intentos:
        registro = intentos_acceso.setdefault(
            clave,
            {"cantidad": 0, "bloqueado_hasta": 0},
        )
        registro["cantidad"] += 1
        if registro["cantidad"] >= current_app.config["MAX_INTENTOS_LOGIN"]:
            registro["cantidad"] = 0
            registro["bloqueado_hasta"] = (
                ahora + current_app.config["SEGUNDOS_BLOQUEO_LOGIN"]
            )
            return True
    return False


def requiere_administrador(funcion):
    # PERMITE EJECUTAR UNA OPERACION SOLAMENTE A LA CUENTA ADMINISTRATIVA.

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
    # VALIDA LAS CREDENCIALES ADMINISTRATIVAS ANTES DE INGRESAR.

    # ============================================================
    # BLOQUE: VALIDACION DEL ACCESO ADMINISTRATIVO
    # Este bloque compara los datos del formulario con la cuenta
    # configurada para el proyecto y crea la sesion del usuario.
    # ============================================================
    if session.get("usuario_admin"):
        return redirect(url_for("inicio.mostrar_modulo", modulo="resumen"))

    mensaje_error = None
    estado_http = 200

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        clave = clave_intento(usuario)

        if acceso_bloqueado(clave):
            return render_template(
                "login.html",
                mensaje_error="Demasiados intentos. Intenta nuevamente más tarde.",
            ), 429

        usuario_valido = compare_digest(usuario, current_app.config["ADMIN_USUARIO"])
        password_valido = compare_digest(
            password,
            current_app.config["ADMIN_PASSWORD"],
        )

        if usuario_valido and password_valido:
            with bloqueo_intentos:
                intentos_acceso.pop(clave, None)
            session.clear()
            session["usuario_admin"] = usuario
            return redirect(url_for("inicio.mostrar_modulo", modulo="resumen"))

        if registrar_fallo(clave):
            mensaje_error = "Demasiados intentos. Intenta nuevamente más tarde."
            estado_http = 429
        else:
            mensaje_error = "Usuario o contraseña incorrectos."
            estado_http = 401

    return render_template("login.html", mensaje_error=mensaje_error), estado_http


@autenticacion_bp.post("/logout")
def logout():
    # CIERRA LA SESION ADMINISTRATIVA Y REGRESA AL LOGIN.

    # ============================================================
    # BLOQUE: CIERRE DE SESION
    # Este bloque elimina los datos de acceso guardados en Flask
    # para impedir que el navegador conserve una sesion anterior.
    # ============================================================
    session.clear()
    return redirect(url_for("autenticacion.login"))
