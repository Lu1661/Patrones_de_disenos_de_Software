"""Pruebas unitarias del servicio que prepara los reportes."""

from datetime import date
from decimal import Decimal

from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.entidades.filial import Filial
from aplicacion.dominio.entidades.producto_importado import ProductoImportado
from aplicacion.dominio.entidades.transaccion_venta import TransaccionVenta
from aplicacion.reportes.servicio_reportes import ServicioReportes
from aplicacion.servicios.fachada_serf import FachadaSERF


class RepositorioListaFalso:
    """Repositorio minimo para entregar una lista controlada."""

    def __init__(self, elementos):
        self._elementos = elementos

    def listar(self):
        return self._elementos


class RepositorioVentasFalso:
    """Consulta ventas en memoria respetando el filtro por filial."""

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
        sku="LAP-001",
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
