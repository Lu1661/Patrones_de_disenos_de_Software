# PRUEBAS DEL CALCULO AUTOMATICO DEL PRECIO LOCAL.

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from aplicacion.dominio.entidades.filial import Filial
from aplicacion.dominio.entidades.tipo_cambio import TipoCambio
from aplicacion.servicios.servicio_productos import ServicioProductos


def test_precio_local_agrega_veinte_por_ciento_y_convierte_a_soles():
    administrador = MagicMock()
    repositorio_productos = MagicMock()
    repositorio_inventario = MagicMock()
    repositorio_filiales = MagicMock()
    repositorio_tasas = MagicMock()

    repositorio_filiales.obtener_por_id.return_value = Filial(
        codigo="PE-LIM-01",
        nombre="Filial Lima",
        pais="Peru",
        ciudad="Lima",
        codigo_divisa="PEN",
        id_filial=1,
    )
    tasas = {
        "CNY": TipoCambio("CNY", "0.14000000", date.today()),
        "PEN": TipoCambio("PEN", "0.25000000", date.today()),
    }
    repositorio_tasas.obtener_vigente.side_effect = (
        lambda codigo, _fecha: tasas.get(codigo)
    )

    def asignar_id(producto, _conexion):
        producto.id_producto = 1

    repositorio_productos.crear.side_effect = asignar_id
    servicio = ServicioProductos(
        administrador,
        repositorio_productos,
        repositorio_inventario,
        repositorio_filiales,
        repositorio_tasas,
    )

    _producto, inventario = servicio.registrar_con_stock(
        {
            "codigo": "LAP-001",
            "nombre": "Laptop",
            "descripcion_tecnica": "Equipo de prueba",
            "categoria": "Laptop",
            "costo_unitario_cny": "100.00",
            "proveedor": "Proveedor",
            "fecha_importacion": date.today().isoformat(),
            "id_filial": 1,
            "stock_inicial": 10,
        }
    )

    assert inventario.precio_venta_local == Decimal("67.20")
    repositorio_inventario.crear.assert_called_once()
