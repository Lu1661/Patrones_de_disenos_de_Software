# CONTROLADOR DEL ACCESO Y LOS PERMISOS DEL SISTEMA.

from functools import wraps
from hmac import compare_digest
from math import ceil
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


PERMISOS_POR_ROL = {
    "administrador": (
        "resumen",
        "configuracion",
        "productos",
        "inventario",
        "ventas",
        "reportes",
    ),
    "supervisor": (
        "resumen",
        "productos",
        "inventario",
        "ventas",
        "reportes",
    ),
    "vendedor": (
        "resumen",
        "productos",
        "ventas",
    ),
}

NOMBRES_ROL = {
    "administrador": "Administrador",
    "supervisor": "Supervisor",
    "vendedor": "Vendedor",
}


def clave_intento(usuario: str = "") -> str:
    # IDENTIFICA LOS INTENTOS POR DIRECCION Y CUENTA INGRESADA.

    direccion = request.remote_addr or "desconocida"
    cuenta = usuario.strip().lower() or "sin_usuario"
    return f"{direccion}:{cuenta}"


def intentos_disponibles(clave: str) -> int:
    # INFORMA CUANTOS INTENTOS QUEDAN ANTES DEL BLOQUEO.

    with bloqueo_intentos:
        registro = intentos_acceso.get(clave)
        usados = registro["cantidad"] if registro else 0
    return max(0, current_app.config["MAX_INTENTOS_LOGIN"] - usados)


def segundos_bloqueo_restantes(clave: str) -> int:
    # CALCULA CUANTO TIEMPO FALTA PARA VOLVER A INTENTAR EL ACCESO.

    ahora = time()
    with bloqueo_intentos:
        registro = intentos_acceso.get(clave)
        if not registro:
            return 0
        if registro["bloqueado_hasta"] > ahora:
            return ceil(registro["bloqueado_hasta"] - ahora)
        if registro["bloqueado_hasta"]:
            intentos_acceso.pop(clave, None)
    return 0


def registrar_fallo(clave: str) -> tuple[bool, int]:
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
            return True, 0
        restantes = current_app.config["MAX_INTENTOS_LOGIN"] - registro["cantidad"]
    return False, restantes


def requiere_administrador(funcion):
    # PERMITE EJECUTAR UNA OPERACION SOLAMENTE A LA CUENTA ADMINISTRATIVA.

    @wraps(funcion)
    def funcion_protegida(*args, **kwargs):
        # ============================================================
        # BLOQUE: AUTORIZACION DE OPERACIONES ADMINISTRATIVAS
        # Este bloque protege las modificaciones aunque alguien intente
        # llamar la API directamente sin utilizar los botones del sistema.
        # ============================================================
        if session.get("rol") != "administrador":
            return jsonify(
                {
                    "exito": False,
                    "mensaje": "Esta operacion requiere un usuario administrador.",
                }
            ), 403
        return funcion(*args, **kwargs)

    return funcion_protegida


def requiere_permiso(modulo: str):
    # PROTEGE UN ENDPOINT SEGUN LOS MODULOS ASIGNADOS AL ROL.

    def decorador(funcion):
        @wraps(funcion)
        def funcion_protegida(*args, **kwargs):
            if modulo not in session.get("permisos", []):
                return jsonify(
                    {
                        "exito": False,
                        "mensaje": "Tu rol no tiene permiso para esta operacion.",
                    }
                ), 403
            return funcion(*args, **kwargs)

        return funcion_protegida

    return decorador


def obtener_cuentas_configuradas() -> tuple[dict, ...]:
    # ARMA LAS CUENTAS DESDE VARIABLES PRIVADAS DEL ENTORNO.

    return (
        {
            "usuario": current_app.config["ADMIN_USUARIO"],
            "password": current_app.config["ADMIN_PASSWORD"],
            "rol": "administrador",
        },
        {
            "usuario": current_app.config["SUPERVISOR_USUARIO"],
            "password": current_app.config["SUPERVISOR_PASSWORD"],
            "rol": "supervisor",
        },
        {
            "usuario": current_app.config["VENDEDOR_USUARIO"],
            "password": current_app.config["VENDEDOR_PASSWORD"],
            "rol": "vendedor",
        },
    )


@autenticacion_bp.route("/login", methods=["GET", "POST"])
def login():
    # VALIDA LAS CREDENCIALES Y GUARDA EL ROL CORRESPONDIENTE.

    # ============================================================
    # BLOQUE: VALIDACION DEL ACCESO ADMINISTRATIVO
    # Este bloque compara los datos del formulario con la cuenta
    # configurada para el proyecto y crea la sesion del usuario.
    # ============================================================
    if session.get("usuario"):
        return redirect(url_for("inicio.mostrar_modulo", modulo="resumen"))

    mensaje_error = None
    estado_http = 200
    segundos_bloqueo = 0
    intentos_restantes = current_app.config["MAX_INTENTOS_LOGIN"]

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        clave = clave_intento(usuario)
        segundos_bloqueo = segundos_bloqueo_restantes(clave)

        if segundos_bloqueo:
            return render_template(
                "login.html",
                mensaje_error="Acceso bloqueado temporalmente.",
                intentos_restantes=0,
                segundos_bloqueo=segundos_bloqueo,
            ), 429

        cuenta_valida = None
        for cuenta in obtener_cuentas_configuradas():
            usuario_configurado = cuenta["usuario"]
            password_configurado = cuenta["password"]
            if not usuario_configurado or not password_configurado:
                continue
            usuario_valido = compare_digest(usuario, usuario_configurado)
            password_valido = compare_digest(password, password_configurado)
            if usuario_valido and password_valido:
                cuenta_valida = cuenta
                break

        if cuenta_valida:
            with bloqueo_intentos:
                intentos_acceso.pop(clave, None)
            session.clear()
            rol = cuenta_valida["rol"]
            session["usuario"] = cuenta_valida["usuario"]
            session["rol"] = rol
            session["nombre_rol"] = NOMBRES_ROL[rol]
            session["permisos"] = list(PERMISOS_POR_ROL[rol])
            return redirect(url_for("inicio.mostrar_modulo", modulo="resumen"))

        bloqueado, intentos_restantes = registrar_fallo(clave)
        if bloqueado:
            mensaje_error = "Acceso bloqueado temporalmente."
            segundos_bloqueo = current_app.config["SEGUNDOS_BLOQUEO_LOGIN"]
            estado_http = 429
        else:
            mensaje_error = "Usuario o contraseña incorrectos."
            estado_http = 401

    return render_template(
        "login.html",
        mensaje_error=mensaje_error,
        intentos_restantes=intentos_restantes,
        segundos_bloqueo=segundos_bloqueo,
    ), estado_http


@autenticacion_bp.post("/logout")
def logout():
    # CIERRA LA SESION ACTUAL Y REGRESA AL LOGIN.

    # ============================================================
    # BLOQUE: CIERRE DE SESION
    # Este bloque elimina los datos de acceso guardados en Flask
    # para impedir que el navegador conserve una sesion anterior.
    # ============================================================
    session.clear()
    return redirect(url_for("autenticacion.login"))
