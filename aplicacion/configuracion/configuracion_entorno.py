"""Lectura segura de variables del entorno local."""

import os

from dotenv import load_dotenv


load_dotenv()


class ConfiguracionEntorno:
    """Valores tecnicos necesarios para iniciar Flask."""

    SECRET_KEY = os.getenv("CLAVE_SECRETA", "clave-local-solo-desarrollo")
    ADMIN_USUARIO = os.getenv("ADMIN_USUARIO", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_BASE_DATOS = os.getenv("MYSQL_BASE_DATOS", "financorp_db")
    MYSQL_USUARIO = os.getenv("MYSQL_USUARIO", "")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")

