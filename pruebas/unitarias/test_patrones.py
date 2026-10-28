# PRUEBAS TC-01 A TC-06 DE LOS PATRONES SOLICITADOS.

import re
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from aplicacion.configuracion.configuracion_global import ConfiguracionGlobal
from aplicacion.reportes.constructor_reporte import (
    DirectorReporte,
    ReporteFinancieroBuilder,
)
from aplicacion.reportes.estructura_reporte import (
    RegistroVentaHoja,
    SeccionCompuesta,
)
from aplicacion.reportes.modelos_reporte import ReporteMensual
from aplicacion.reportes.personalizacion_reporte import (
    FirmaDigitalDecorator,
    MarcaDeAguaDecorator,
)
from aplicacion.servicios.fachada_serf import FachadaSERF


def crear_estructura_ejemplo() -> SeccionCompuesta:
    # CREA UN ARBOL PEQUENO QUE VARIAS PRUEBAS PUEDEN REUTILIZAR.

    raiz = SeccionCompuesta("Consolidado corporativo")
    filial = SeccionCompuesta("Filial Lima")
    filial.agregar(
        RegistroVentaHoja(
            nombre="F001-1 - Laptop",
            subtotal_local="200.00",
            tasa_eur="0.25000000",
            codigo_divisa="PEN",
        )
    )
    raiz.agregar(filial)
    return raiz


# ============================================================
# BLOQUE: CASOS TC-01 A TC-06
# Cada prueba conserva el identificador usado por la documentacion para
# que el resultado de pytest pueda relacionarse con la matriz de pruebas.
# ============================================================
def test_tc_01_singleton_devuelve_la_misma_instancia_en_varios_hilos():
    with ThreadPoolExecutor(max_workers=8) as ejecutor:
        instancias = list(
            ejecutor.map(
                lambda _indice: ConfiguracionGlobal.obtener_instancia(),
                range(24),
            )
        )

    primera = instancias[0]
    assert all(instancia is primera for instancia in instancias)


def test_tc_02_prototype_clona_sin_modificar_la_plantilla():
    plantilla = ReporteMensual()
    clon = plantilla.clonar()
    clon.definir_datos_principales("Reporte mensual modificado", "Octubre 2026")
    clon.cuerpo.agregar(
        RegistroVentaHoja("F001-1", "100.00", "0.25000000", "PEN")
    )

    assert clon is not plantilla
    assert clon.titulo == "Reporte mensual modificado"
    assert plantilla.titulo == "Reporte mensual de ingresos"
    assert len(clon.cuerpo.hijos) == 1
    assert len(plantilla.cuerpo.hijos) == 0


def test_tc_03_builder_construye_todas_las_partes_del_reporte():
    director = DirectorReporte(ReporteFinancieroBuilder())
    reporte = director.construir_reporte_completo(
        ReporteMensual().clonar(),
        "Octubre 2026",
        crear_estructura_ejemplo(),
        graficos=["Filial Lima: 50.00 EUR"],
        conclusiones=["El resultado del periodo es positivo."],
    )

    assert reporte.periodo == "Octubre 2026"
    assert reporte.total_eur == Decimal("50.00")
    assert reporte.graficos == ["Filial Lima: 50.00 EUR"]
    assert reporte.conclusiones == ["El resultado del periodo es positivo."]


def test_tc_04_composite_suma_dos_niveles_del_arbol():
    raiz = SeccionCompuesta("Corporacion")
    pais = SeccionCompuesta("Peru")
    filial = SeccionCompuesta("Filial Lima")
    filial.agregar(RegistroVentaHoja("Venta 1", "100.00", "0.25000000", "PEN"))
    filial.agregar(RegistroVentaHoja("Venta 2", "80.00", "0.25000000", "PEN"))
    pais.agregar(filial)
    raiz.agregar(pais)

    assert raiz.calcular_total_eur() == Decimal("45.00")
    assert "Filial Lima - Total: 45.00 EUR" in raiz.renderizar()


def test_tc_05_decorator_agrega_marca_de_agua_y_firma_sha256():
    reporte = ReporteMensual()
    decorado = FirmaDigitalDecorator(MarcaDeAguaDecorator(reporte))

    contenido = decorado.emitir()

    assert contenido.startswith("[MARCA DE AGUA: CONFIDENCIAL - FINANCORP S.A.]")
    assert "FIRMA DIGITAL ACADEMICA" in contenido
    assert re.search(r"SHA-256: [a-f0-9]{64}$", contenido)


def test_tc_06_facade_genera_el_reporte_con_una_sola_llamada():
    contenido = FachadaSERF().emitir_reporte_consolidado(
        "mensual",
        "Octubre 2026",
        crear_estructura_ejemplo(),
        con_marca_agua=True,
        con_firma=True,
        graficos=["Filial Lima: 50.00 EUR"],
        conclusiones=["Reporte generado correctamente."],
    )

    assert "Reporte mensual de ingresos" in contenido
    assert "TOTAL CONSOLIDADO: 50.00 EUR" in contenido
    assert "MARCA DE AGUA" in contenido
    assert "SHA-256" in contenido
