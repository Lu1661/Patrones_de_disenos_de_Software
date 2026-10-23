"""Contratos estrictamente necesarios para generar reportes."""

from abc import ABC, abstractmethod
from typing import Any


class IReportePrototype(ABC):
    """Contrato minimo para clonar una plantilla de reporte."""

    @abstractmethod
    def clonar(self) -> "IReportePrototype":
        """Retorna una copia profunda independiente de la plantilla."""


class IReporteFinanciero(ABC):
    """Contrato comun del reporte base y sus personalizaciones."""

    @abstractmethod
    def emitir(self) -> str:
        """Retorna el contenido final listo para visualizar o exportar."""


class IReporteBuilder(ABC):
    """Pasos indispensables para ensamblar un reporte financiero."""

    @abstractmethod
    def reset(self, reporte_inicial: Any | None = None) -> None:
        """Reinicia la construccion desde una plantilla."""

    @abstractmethod
    def definir_encabezado(self, titulo: str, periodo: str) -> None:
        """Establece el titulo y el periodo del reporte."""

    @abstractmethod
    def construir_cuerpo_consolidado(self, secciones: Any) -> None:
        """Asigna la estructura jerarquica del reporte."""

    @abstractmethod
    def agregar_graficos(self, graficos: list[str]) -> None:
        """Agrega las descripciones de los graficos requeridos."""

    @abstractmethod
    def agregar_conclusiones(self, conclusiones: list[str]) -> None:
        """Agrega las conclusiones financieras del periodo."""

    @abstractmethod
    def agregar_totales(self) -> None:
        """Calcula y conserva el total en EUR."""

    @abstractmethod
    def obtener_resultado(self) -> IReporteFinanciero:
        """Entrega el reporte terminado."""

