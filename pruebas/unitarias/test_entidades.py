# PRUEBAS UNITARIAS DE LAS REGLAS PRINCIPALES DEL DOMINIO.

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.entidades.inventario_filial import InventarioFilial
from aplicacion.dominio.entidades.producto_importado import ProductoImportado
from aplicacion.dominio.entidades.tipo_cambio import TipoCambio
from aplicacion.dominio.entidades.transaccion_venta import TransaccionVenta
from aplicacion.servicios.servicio_tipo_cambio import ServicioTiposCambio


# ============================================================
# BLOQUE: PRUEBAS DE ENTIDADES Y CALCULOS DEL NEGOCIO
# Estas pruebas comprueban conversiones, stock, totales y fechas sin
# depender de Flask ni de una conexion a MySQL.
# ============================================================
def test_producto_convierte_costo_cny_a_eur():
    producto = ProductoImportado.crear_con_conversion(
        codigo="LAP-001",
        nombre="Laptop de prueba",
        descripcion_tecnica="Equipo para prueba unitaria",
        categoria="Laptop",
        costo_unitario_cny="100.00",
        tasa_cny_eur="0.13000000",
        proveedor="Proveedor de prueba",
        fecha_importacion=date.today(),
    )

    assert producto.codigo == "LAP-001"
    assert producto.costo_unitario_cny == Decimal("100.00")
    assert producto.costo_unitario_eur == Decimal("13.00")


def test_inventario_impide_stock_negativo():
    inventario = InventarioFilial(
        id_filial=1,
        id_producto=1,
        stock_disponible=5,
        precio_venta_local="120.00",
    )

    with pytest.raises(ValueError, match="Stock insuficiente"):
        inventario.descontar_stock(6)

    assert inventario.stock_disponible == 5
    inventario.descontar_stock(2)
    assert inventario.stock_disponible == 3


def test_venta_calcula_ingresos_gastos_y_resultado_en_eur():
    detalle = DetalleVenta(
        id_producto=1,
        cantidad=2,
        precio_unitario_local="120.00",
        costo_unitario_eur="13.00",
    )
    venta = TransaccionVenta(
        numero_factura="F001-1",
        id_filial=1,
        fecha_venta=date.today(),
        cliente="Cliente de prueba",
        vendedor="Vendedor de prueba",
        metodo_pago="Tarjeta",
        codigo_divisa="PEN",
        tasa_eur_aplicada="0.25000000",
        detalles=[detalle],
    )

    assert venta.total_local == Decimal("240.00")
    assert venta.total_eur == Decimal("60.00")
    assert venta.total_costo_eur == Decimal("26.00")
    assert venta.resultado_financiero_eur == Decimal("34.00")


def test_producto_rechaza_fecha_futura_y_categoria_desconocida():
    datos = {
        "codigo": "LAP-002",
        "nombre": "Laptop futura",
        "descripcion_tecnica": "Equipo para validar errores",
        "categoria": "Laptop",
        "costo_unitario_cny": "100.00",
        "tasa_cny_eur": "0.13000000",
        "proveedor": "Proveedor de prueba",
        "fecha_importacion": date.today() + timedelta(days=1),
    }

    with pytest.raises(ValueError, match="fecha futura"):
        ProductoImportado.crear_con_conversion(**datos)

    datos["fecha_importacion"] = date.today()
    datos["categoria"] = "Electrodomestico"
    with pytest.raises(ValueError, match="categoria"):
        ProductoImportado.crear_con_conversion(**datos)


def test_tipo_cambio_admite_una_vigencia_futura():
    tasa_programada = TipoCambio(
        codigo_divisa_origen="CNY",
        tasa="0.15000000",
        fecha_vigencia=date.today() + timedelta(days=1),
    )

    assert tasa_programada.fecha_vigencia == date.today() + timedelta(days=1)


def test_tasa_futura_no_reemplaza_la_tasa_actual_del_singleton():
    repositorio = Mock()
    configuracion = Mock()
    tasa_actual = TipoCambio(
        codigo_divisa_origen="CNY",
        tasa="0.14000000",
        fecha_vigencia=date.today(),
    )
    repositorio.obtener_vigente.return_value = tasa_actual
    servicio = ServicioTiposCambio(repositorio, configuracion)

    servicio.registrar(
        {
            "codigo_divisa_origen": "CNY",
            "tasa": "0.15000000",
            "fecha_vigencia": (date.today() + timedelta(days=1)).isoformat(),
        }
    )

    configuracion.actualizar_tasa.assert_called_once_with(
        "CNY",
        Decimal("0.14000000"),
    )
