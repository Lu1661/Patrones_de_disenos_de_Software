# PRUEBAS UNITARIAS DEL SERVICIO QUE PREPARA LOS REPORTES.

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.entidades.filial import Filial
from aplicacion.dominio.entidades.producto_importado import ProductoImportado
from aplicacion.dominio.entidades.transaccion_venta import TransaccionVenta
from aplicacion.reportes.servicio_reportes import ServicioReportes
from aplicacion.servicios.fachada_serf import FachadaSERF


class RepositorioListaFalso:
    # REPOSITORIO MINIMO PARA ENTREGAR UNA LISTA CONTROLADA.

    def __init__(self, elementos):
        self._elementos = elementos

    def listar(self):
        return self._elementos


class RepositorioVentasFalso:
    # CONSULTA VENTAS EN MEMORIA RESPETANDO EL FILTRO POR FILIAL.

    def __init__(self, ventas):
        self._ventas = ventas

    def listar_por_periodo(self, _inicio, _fin, id_filial=None):
        if id_filial is None:
            return self._ventas
        return [venta for venta in self._ventas if venta.id_filial == id_filial]


def crear_servicio_con_una_venta(
    incluir_venta: bool = True,
) -> ServicioReportes:
    filial = Filial(
        codigo="PE-LIM-01",
        nombre="Filial Lima",
        pais="Peru",
        ciudad="Lima",
        codigo_divisa="PEN",
        id_filial=1,
    )
    producto = ProductoImportado(
        codigo="LAP-001",
        nombre="Laptop de prueba",
        descripcion_tecnica="Equipo para el reporte unitario",
        categoria="Laptop",
        costo_unitario_cny=Decimal("100.00"),
        costo_unitario_eur=Decimal("13.00"),
        proveedor="Proveedor de prueba",
        fecha_importacion=date.today(),
        id_producto=1,
    )
    venta = TransaccionVenta(
        numero_factura="F001-1",
        id_filial=1,
        fecha_venta=date.today(),
        cliente="Cliente de prueba",
        vendedor="Vendedor de prueba",
        metodo_pago="Efectivo",
        codigo_divisa="PEN",
        tasa_eur_aplicada=Decimal("0.25000000"),
        detalles=[DetalleVenta(1, 2, Decimal("120.00"), Decimal("13.00"))],
        id_venta=1,
    )
    return ServicioReportes(
        RepositorioVentasFalso([venta] if incluir_venta else []),
        RepositorioListaFalso([filial]),
        RepositorioListaFalso([producto]),
        FachadaSERF(),
    )


# ============================================================
# BLOQUE: RESULTADOS FINANCIEROS DEL REPORTE
# Comprueba el contenido estructurado que recibira el frontend sin usar
# datos externos ni modificar una base de datos.
# ============================================================
def test_servicio_calcula_totales_y_estructura_del_reporte():
    servicio = crear_servicio_con_una_venta()

    reporte = servicio.generar(
        {
            "tipo": "mensual",
            "anio": date.today().year,
            "mes": date.today().month,
            "id_filial": "",
            "con_marca_agua": True,
            "con_firma": True,
        }
    )

    assert reporte["cantidad_ventas"] == 1
    assert reporte["total_ingresos_eur"] == Decimal("60.00")
    assert reporte["total_gastos_eur"] == Decimal("26.00")
    assert reporte["resultado_financiero_eur"] == Decimal("34.00")
    assert "Peru" in reporte["contenido_emitido"]
    assert "Filial Lima" in reporte["contenido_emitido"]
    assert "Laptop" in reporte["contenido_emitido"]
    assert len(reporte["firma"]["sha256"]) == 64


def test_servicio_genera_reporte_vacio_para_filial_sin_ventas():
    servicio = crear_servicio_con_una_venta(incluir_venta=False)

    reporte = servicio.generar(
        {
            "tipo": "anual",
            "anio": date.today().year,
            "id_filial": 1,
            "con_marca_agua": False,
            "con_firma": False,
        }
    )

    assert reporte["cantidad_ventas"] == 0
    assert reporte["total_ingresos_eur"] == Decimal("0.00")
    assert reporte["resultado_financiero_eur"] == Decimal("0.00")
    assert "Sin movimientos registrados" in reporte["contenido_emitido"]


def test_detalle_del_reporte_se_ordena_por_filial_categoria_importe_y_fecha():
    def crear_venta(factura, filial, fecha, producto, total):
        detalle = SimpleNamespace(
            id_producto=producto,
            cantidad=1,
            subtotal_local=Decimal(total),
            subtotal_costo_eur=Decimal("10.00"),
        )
        return SimpleNamespace(
            numero_factura=factura,
            id_filial=filial,
            fecha_venta=fecha,
            codigo_divisa="PEN",
            tasa_eur_aplicada=Decimal("0.25"),
            detalles=[detalle],
        )

    ventas = [
        crear_venta("F-04", 2, datetime(2026, 1, 4, 10, 0), 3, "900.00"),
        crear_venta("F-03", 1, datetime(2026, 1, 5, 10, 0), 1, "300.00"),
        crear_venta("F-01", 1, datetime(2026, 1, 3, 10, 0), 1, "500.00"),
        crear_venta("F-02", 1, datetime(2026, 1, 2, 10, 0), 1, "300.00"),
        crear_venta("F-05", 1, datetime(2026, 1, 1, 10, 0), 2, "700.00"),
    ]
    filiales = {
        1: SimpleNamespace(nombre="Filial Alfa"),
        2: SimpleNamespace(nombre="Filial Beta"),
    }
    productos = {
        1: SimpleNamespace(nombre="Laptop", categoria="Laptop"),
        2: SimpleNamespace(nombre="Telefono", categoria="Smartphone"),
        3: SimpleNamespace(nombre="Router", categoria="Redes"),
    }

    filas = ServicioReportes._preparar_ventas(ventas, filiales, productos)

    assert [fila["numero_factura"] for fila in filas] == [
        "F-01",
        "F-02",
        "F-03",
        "F-05",
        "F-04",
    ]
