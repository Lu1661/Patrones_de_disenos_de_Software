"""Estructura jerarquica de secciones y registros del reporte."""

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
    """Contrato comun para secciones y registros individuales."""

    def __init__(self, nombre: str) -> None:
        self.nombre = limpiar_texto(nombre, "nombre del componente")

    @abstractmethod
    def calcular_total_eur(self) -> Decimal:
        """Retorna el valor del componente expresado en EUR."""

    @abstractmethod
    def renderizar(self, nivel: int = 0) -> str:
        """Retorna una representacion textual respetando la jerarquia."""


@dataclass
class RegistroVentaHoja(ComponenteReporte):
    """Elemento final del arbol que representa un importe de venta."""

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
        """Convierte directamente el valor de la hoja a EUR."""

        return redondear_moneda(self.subtotal_local * self.tasa_eur)

    def renderizar(self, nivel: int = 0) -> str:
        """Muestra la venta con su monto local y total en EUR."""

        sangria = "  " * nivel
        return (
            f"{sangria}- {self.nombre}: "
            f"{redondear_moneda(self.subtotal_local)} {self.codigo_divisa} "
            f"= {self.calcular_total_eur()} EUR"
        )


@dataclass
class SeccionCompuesta(ComponenteReporte):
    """Agrupacion que puede contener otras secciones o registros."""

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
        """Expone una vista que no permite modificar la lista interna."""

        return tuple(self._hijos)

    def agregar(self, hijo: ComponenteReporte) -> None:
        """Agrega una seccion o una hoja valida al arbol."""

        if not isinstance(hijo, ComponenteReporte):
            raise ValueError("Solo se pueden agregar componentes de reporte.")
        self._hijos.append(hijo)

    def remover(self, hijo: ComponenteReporte) -> None:
        """Retira un componente previamente agregado."""

        self._hijos.remove(hijo)

    def calcular_total_eur(self) -> Decimal:
        """Suma recursivamente todos los elementos contenidos."""

        total = sum(
            (hijo.calcular_total_eur() for hijo in self._hijos),
            Decimal("0"),
        )
        return redondear_moneda(total)

    def renderizar(self, nivel: int = 0) -> str:
        """Representa la seccion y sus descendientes con sangria."""

        sangria = "  " * nivel
        lineas = [f"{sangria}{self.nombre} - Total: {self.calcular_total_eur()} EUR"]
        if not self._hijos:
            lineas.append(f"{sangria}  Sin movimientos registrados")
        else:
            lineas.extend(hijo.renderizar(nivel + 1) for hijo in self._hijos)
        return "\n".join(lineas)

