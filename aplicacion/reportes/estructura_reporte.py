# ESTRUCTURA JERARQUICA DE SECCIONES Y REGISTROS DEL REPORTE.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal

from aplicacion.dominio.validaciones import (
    limpiar_texto,
    normalizar_codigo_iso,
    redondear_moneda,
    redondear_tasa,
    validar_decimal_no_negativo,
)


class ComponenteReporte(ABC):
    # CONTRATO COMUN PARA SECCIONES Y REGISTROS INDIVIDUALES.

    def __init__(self, nombre: str) -> None:
        self.nombre = limpiar_texto(nombre, "nombre del componente")

    @abstractmethod
    def calcular_total_eur(self) -> Decimal:
        # DEVUELVE EL VALOR DEL COMPONENTE EXPRESADO EN EUR.
        pass

    @abstractmethod
    def renderizar(self, nivel: int = 0) -> str:
        # DEVUELVE UNA REPRESENTACION TEXTUAL RESPETANDO LA JERARQUIA.
        pass


@dataclass
class RegistroVentaHoja(ComponenteReporte):
    # ELEMENTO FINAL DEL ARBOL QUE REPRESENTA UN IMPORTE DE VENTA.

    nombre: str
    subtotal_local: Decimal
    tasa_eur: Decimal
    codigo_divisa: str

    def __post_init__(self) -> None:
        ComponenteReporte.__init__(self, self.nombre)
        self.subtotal_local = validar_decimal_no_negativo(
            self.subtotal_local,
            "subtotal local",
        )
        self.tasa_eur = redondear_tasa(self.tasa_eur)
        self.codigo_divisa = normalizar_codigo_iso(self.codigo_divisa)

    def calcular_total_eur(self) -> Decimal:
        # CONVIERTE DIRECTAMENTE EL VALOR DE LA HOJA A EUR.

        return redondear_moneda(self.subtotal_local * self.tasa_eur)

    def renderizar(self, nivel: int = 0) -> str:
        # MUESTRA LA VENTA CON SU MONTO LOCAL Y TOTAL EN EUR.

        sangria = "  " * nivel
        return (
            f"{sangria}- {self.nombre}: "
            f"{redondear_moneda(self.subtotal_local)} {self.codigo_divisa} "
            f"= {self.calcular_total_eur()} EUR"
        )


@dataclass
class SeccionCompuesta(ComponenteReporte):
    # AGRUPACION QUE PUEDE CONTENER OTRAS SECCIONES O REGISTROS.

    nombre: str
    _hijos: list[ComponenteReporte] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        # ============================================================
        # PATRON COMPOSITE: ARBOL DEL REPORTE FINANCIERO
        # Este bloque permite tratar igual una agrupacion completa y
        # una venta individual al calcular o mostrar el consolidado.
        # Cumple: RF-07 y CU-08.
        # ============================================================
        ComponenteReporte.__init__(self, self.nombre)
        hijos_recibidos = list(self._hijos)
        self._hijos = []
        for hijo in hijos_recibidos:
            self.agregar(hijo)

    @property
    def hijos(self) -> tuple[ComponenteReporte, ...]:
        # EXPONE UNA VISTA QUE NO PERMITE MODIFICAR LA LISTA INTERNA.

        return tuple(self._hijos)

    def agregar(self, hijo: ComponenteReporte) -> None:
        # AGREGA UNA SECCION O UNA HOJA VALIDA AL ARBOL.

        if not isinstance(hijo, ComponenteReporte):
            raise ValueError("Solo se pueden agregar componentes de reporte.")
        self._hijos.append(hijo)

    def remover(self, hijo: ComponenteReporte) -> None:
        # RETIRA UN COMPONENTE PREVIAMENTE AGREGADO.

        self._hijos.remove(hijo)

    def calcular_total_eur(self) -> Decimal:
        # SUMA RECURSIVAMENTE TODOS LOS ELEMENTOS CONTENIDOS.

        total = sum(
            (hijo.calcular_total_eur() for hijo in self._hijos),
            Decimal("0"),
        )
        return redondear_moneda(total)

    def renderizar(self, nivel: int = 0) -> str:
        # REPRESENTA LA SECCION Y SUS DESCENDIENTES CON SANGRIA.

        sangria = "  " * nivel
        lineas = [f"{sangria}{self.nombre} - Total: {self.calcular_total_eur()} EUR"]
        if not self._hijos:
            lineas.append(f"{sangria}  Sin movimientos registrados")
        else:
            lineas.extend(hijo.renderizar(nivel + 1) for hijo in self._hijos)
        return "\n".join(lineas)

