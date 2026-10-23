"""Prueba integral y reversible de la API conectada a MySQL."""

import os
import secrets
from datetime import date, datetime, timedelta

import mysql.connector
import pytest
from dotenv import load_dotenv


load_dotenv()


VARIABLES_MYSQL = (
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_BASE_DATOS",
    "MYSQL_USUARIO",
    "MYSQL_PASSWORD",
)


def mysql_configurado() -> bool:
    """Indica si el entorno permite ejecutar la prueba de integracion."""

    return all(os.getenv(nombre) for nombre in VARIABLES_MYSQL)


pytestmark = [
    pytest.mark.integracion,
    pytest.mark.skipif(
        not mysql_configurado(),
        reason="MySQL no esta configurado mediante variables de entorno.",
    ),
]


# ============================================================
# BLOQUE: FLUJO COMPLETO Y REVERSIBLE SOBRE MYSQL
# Registra tasas, filial, producto y venta mediante Flask; comprueba
# transacciones y reportes; finalmente elimina todos los datos creados.
# ============================================================
def test_flujo_completo_api_mysql():
    from aplicacion.crear_aplicacion import crear_aplicacion

    conexion = mysql.connector.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        database=os.environ["MYSQL_BASE_DATOS"],
        user=os.environ["MYSQL_USUARIO"],
        password=os.environ["MYSQL_PASSWORD"],
    )
    conexion.autocommit = False
    cursor = conexion.cursor(dictionary=True)
    sufijo = secrets.token_hex(4).upper()
    codigo_filial = f"PY-{sufijo}"
    sku = f"PY-SKU-{sufijo}"
    factura = f"PY-FV-{sufijo}"
    ids_activos = {}
    ids_tasas = []

    try:
        for divisa in ("CNY", "PEN"):
            cursor.execute(
                "SELECT id_tipo_cambio FROM tipos_cambio "
                "WHERE codigo_divisa_origen=%s AND activa=TRUE",
                (divisa,),
            )
            ids_activos[divisa] = [
                fila["id_tipo_cambio"] for fila in cursor.fetchall()
            ]

        fecha_tasa = date.today()
        while True:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM tipos_cambio "
                "WHERE codigo_divisa_origen IN ('CNY','PEN') "
                "AND fecha_vigencia=%s",
                (fecha_tasa,),
            )
            if cursor.fetchone()["total"] == 0:
                break
            fecha_tasa -= timedelta(days=1)

        # Finaliza la lectura inicial para que esta conexion pueda ver
        # posteriormente los registros confirmados por la API de Flask.
        conexion.commit()

        aplicacion = crear_aplicacion()
        aplicacion.config.update(
            TESTING=True,
            ADMIN_USUARIO="admin",
            ADMIN_PASSWORD="admin",
        )
        cliente = aplicacion.test_client()
        acceso = cliente.post(
            "/login",
            data={"usuario": "admin", "password": "admin"},
        )
        assert acceso.status_code == 302

        def publicar(ruta: str, datos: dict, estado: int):
            respuesta = cliente.post(ruta, json=datos)
            assert respuesta.status_code == estado, respuesta.get_json()
            return respuesta.get_json()

        for divisa, tasa in (("CNY", "0.13000000"), ("PEN", "0.25000000")):
            tipo_cambio = publicar(
                "/api/configuracion/tipos-cambio",
                {
                    "codigo_divisa_origen": divisa,
                    "tasa": tasa,
                    "fecha_vigencia": fecha_tasa.isoformat(),
                },
                201,
            )["datos"]
            ids_tasas.append(tipo_cambio["id_tipo_cambio"])

        filial = publicar(
            "/api/configuracion/filiales",
            {
                "codigo": codigo_filial,
                "nombre": "Filial Pytest",
                "pais": "Peru",
                "ciudad": "Lima",
                "codigo_divisa": "PEN",
            },
            201,
        )["datos"]
        producto_datos = {
            "sku": sku,
            "nombre": "Producto Pytest",
            "descripcion_tecnica": "Producto temporal de integracion",
            "categoria": "Laptop",
            "costo_unitario_cny": "100.00",
            "proveedor": "Proveedor Pytest",
            "fecha_importacion": date.today().isoformat(),
            "id_filial": filial["id_filial"],
            "stock_inicial": 10,
            "precio_venta_local": "120.00",
        }
        producto = publicar("/api/productos", producto_datos, 201)["datos"]["producto"]

        duplicado = publicar("/api/productos", producto_datos, 409)
        assert duplicado["exito"] is False

        venta_datos = {
            "numero_factura": factura,
            "id_filial": filial["id_filial"],
            "id_producto": producto["id_producto"],
            "cantidad": 4,
            "fecha_venta": datetime.now().replace(microsecond=0).isoformat(),
            "cliente": "Cliente Pytest",
            "vendedor": "Vendedor Pytest",
            "metodo_pago": "Tarjeta",
        }
        venta = publicar("/api/ventas", venta_datos, 201)["datos"]
        assert venta["total_local"] == "480.00"
        assert venta["total_eur"] == "120.00"

        inventario = cliente.get(
            f"/api/inventario?id_filial={filial['id_filial']}"
        ).get_json()["datos"]
        assert inventario[0]["stock_disponible"] == 6

        venta_datos["numero_factura"] = f"{factura}-SIN-STOCK"
        venta_datos["cantidad"] = 99
        sin_stock = publicar("/api/ventas", venta_datos, 400)
        assert sin_stock["mensaje"] == "Stock insuficiente. Disponible: 6."

        inventario_final = cliente.get(
            f"/api/inventario?id_filial={filial['id_filial']}"
        ).get_json()["datos"]
        assert inventario_final[0]["stock_disponible"] == 6

        reporte = publicar(
            "/api/reportes/generar",
            {
                "tipo": "mensual",
                "anio": date.today().year,
                "mes": date.today().month,
                "id_filial": filial["id_filial"],
                "con_marca_agua": True,
                "con_firma": True,
            },
            200,
        )["datos"]
        assert reporte["cantidad_ventas"] == 1
        assert reporte["total_ingresos_eur"] == "120.00"
        assert reporte["total_gastos_eur"] == "52.00"
        assert reporte["resultado_financiero_eur"] == "68.00"
        assert len(reporte["firma"]["sha256"]) == 64
    finally:
        try:
            cursor.execute(
                "DELETE FROM ventas WHERE numero_factura LIKE %s",
                (f"{factura}%",),
            )
            cursor.execute(
                "SELECT id_producto FROM productos_importados WHERE sku=%s",
                (sku,),
            )
            productos = [fila["id_producto"] for fila in cursor.fetchall()]
            if productos:
                marcadores = ",".join(["%s"] * len(productos))
                cursor.execute(
                    f"DELETE FROM inventarios_filial "
                    f"WHERE id_producto IN ({marcadores})",
                    tuple(productos),
                )
                cursor.execute(
                    f"DELETE FROM productos_importados "
                    f"WHERE id_producto IN ({marcadores})",
                    tuple(productos),
                )
            cursor.execute("DELETE FROM filiales WHERE codigo=%s", (codigo_filial,))
            if ids_tasas:
                marcadores = ",".join(["%s"] * len(ids_tasas))
                cursor.execute(
                    f"DELETE FROM tipos_cambio "
                    f"WHERE id_tipo_cambio IN ({marcadores})",
                    tuple(ids_tasas),
                )
            for divisa in ("CNY", "PEN"):
                cursor.execute(
                    "UPDATE tipos_cambio SET activa=FALSE "
                    "WHERE codigo_divisa_origen=%s",
                    (divisa,),
                )
                if ids_activos.get(divisa):
                    marcadores = ",".join(["%s"] * len(ids_activos[divisa]))
                    cursor.execute(
                        f"UPDATE tipos_cambio SET activa=TRUE "
                        f"WHERE id_tipo_cambio IN ({marcadores})",
                        tuple(ids_activos[divisa]),
                    )
            conexion.commit()

            cursor.execute(
                "SELECT COUNT(*) AS total FROM filiales WHERE codigo=%s",
                (codigo_filial,),
            )
            assert cursor.fetchone()["total"] == 0
            cursor.execute(
                "SELECT COUNT(*) AS total FROM productos_importados WHERE sku=%s",
                (sku,),
            )
            assert cursor.fetchone()["total"] == 0
            cursor.execute(
                "SELECT COUNT(*) AS total FROM ventas WHERE numero_factura LIKE %s",
                (f"{factura}%",),
            )
            assert cursor.fetchone()["total"] == 0
        finally:
            cursor.close()
            conexion.close()
