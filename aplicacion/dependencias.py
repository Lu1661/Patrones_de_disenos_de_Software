"""Creacion de los objetos que necesita la aplicacion."""

from flask import Flask, current_app
from mysql.connector import Error as ErrorMySQL

from aplicacion.configuracion.configuracion_global import ConfiguracionGlobal
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_filiales import (
    RepositorioFiliales,
)
from aplicacion.persistencia.repositorios.repositorio_inventario import (
    RepositorioInventario,
)
from aplicacion.persistencia.repositorios.repositorio_productos import (
    RepositorioProductos,
)
from aplicacion.persistencia.repositorios.repositorio_tipos_cambio import (
    RepositorioTiposCambio,
)
from aplicacion.persistencia.repositorios.repositorio_ventas import (
    RepositorioVentas,
)
from aplicacion.servicios import (
    ServicioFiliales,
    ServicioInventario,
    ServicioProductos,
    ServicioTiposCambio,
    ServicioVentas,
)


def configurar_dependencias(aplicacion: Flask) -> None:
    """Construye una sola vez los repositorios y servicios del sistema."""

    # ============================================================
    # BLOQUE: UNION DE LAS CAPAS DEL SISTEMA
    # Este bloque entrega a cada servicio solamente los repositorios
    # que necesita y evita crear conexiones dentro de los controladores.
    # ============================================================
    usuario = str(aplicacion.config.get("MYSQL_USUARIO", "")).strip()
    password = str(aplicacion.config.get("MYSQL_PASSWORD", ""))
    base_datos = str(aplicacion.config.get("MYSQL_BASE_DATOS", "")).strip()

    if not usuario or not password or not base_datos:
        aplicacion.extensions["servicios_serf"] = {}
        return

    administrador = ConexionMySQL(
        host=str(aplicacion.config["MYSQL_HOST"]),
        puerto=int(aplicacion.config["MYSQL_PORT"]),
        base_datos=base_datos,
        usuario=usuario,
        password=password,
    )
    repositorio_filiales = RepositorioFiliales(administrador)
    repositorio_tasas = RepositorioTiposCambio(administrador)
    repositorio_productos = RepositorioProductos(administrador)
    repositorio_inventario = RepositorioInventario(administrador)
    repositorio_ventas = RepositorioVentas(administrador)
    configuracion = ConfiguracionGlobal.obtener_instancia()

    servicio_tasas = ServicioTiposCambio(repositorio_tasas, configuracion)
    servicios = {
        "filiales": ServicioFiliales(repositorio_filiales),
        "tipos_cambio": servicio_tasas,
        "productos": ServicioProductos(
            administrador,
            repositorio_productos,
            repositorio_inventario,
            repositorio_filiales,
            repositorio_tasas,
        ),
        "inventario": ServicioInventario(repositorio_inventario),
        "ventas": ServicioVentas(
            administrador,
            repositorio_ventas,
            repositorio_inventario,
            repositorio_productos,
            repositorio_filiales,
            repositorio_tasas,
        ),
    }
    aplicacion.extensions["servicios_serf"] = servicios

    try:
        servicio_tasas.cargar_tasas_activas()
    except ErrorMySQL:
        aplicacion.logger.warning(
            "No fue posible cargar las tasas al iniciar. Se intentara al usar la API."
        )


def obtener_servicio(nombre: str):
    """Recupera un servicio configurado para la solicitud actual."""

    servicios = current_app.extensions.get("servicios_serf", {})
    if nombre not in servicios:
        raise RuntimeError(
            "La conexion MySQL no esta configurada en el entorno local."
        )
    return servicios[nombre]
