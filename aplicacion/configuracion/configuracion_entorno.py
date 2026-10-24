"""Lectura segura de variables del entorno local."""

import os
from secrets import token_hex

from dotenv import load_dotenv


load_dotenv()


def leer_booleano(nombre: str, valor_inicial: bool = False) -> bool:
    """Convierte una variable de entorno sencilla en verdadero o falso."""

    valor = os.getenv(nombre)
    if valor is None:
        return valor_inicial
    return valor.strip().lower() in {"1", "true", "si", "sí", "yes"}


clave_configurada = os.getenv("CLAVE_SECRETA", "").strip()
if not clave_configurada or clave_configurada == "cambiar_en_el_entorno_local":
    clave_configurada = token_hex(32)


class ConfiguracionEntorno:
    """Valores tecnicos necesarios para iniciar Flask."""

    # ============================================================
    # BLOQUE: PROTECCION DE LA SESION LOCAL
    # Este bloque evita una clave fija conocida y configura la cookie
    # administrativa sin impedir la ejecucion local mediante HTTP.
    # ============================================================
    SECRET_KEY = clave_configurada
    SESSION_COOKIE_NAME = "serf_sesion"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = leer_booleano("COOKIE_SEGURA")
    MAX_CONTENT_LENGTH = 1024 * 1024

    ADMIN_USUARIO = os.getenv("ADMIN_USUARIO", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_BASE_DATOS = os.getenv("MYSQL_BASE_DATOS", "financorp_db")
    MYSQL_USUARIO = os.getenv("MYSQL_USUARIO", "")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")

