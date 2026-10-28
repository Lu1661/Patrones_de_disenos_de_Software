# CONTRATOS ESTRICTAMENTE NECESARIOS PARA GENERAR REPORTES.

from abc import ABC, abstractmethod
from typing import Any


class IReportePrototype(ABC):
    # CONTRATO MINIMO PARA CLONAR UNA PLANTILLA DE REPORTE.

    @abstractmethod
    def clonar(self) -> "IReportePrototype":
        # DEVUELVE UNA COPIA PROFUNDA INDEPENDIENTE DE LA PLANTILLA.
        pass


class IReporteFinanciero(ABC):
    # CONTRATO COMUN DEL REPORTE BASE Y SUS PERSONALIZACIONES.

    @abstractmethod
    def emitir(self) -> str:
        # DEVUELVE EL CONTENIDO FINAL LISTO PARA VISUALIZAR O EXPORTAR.
        pass


class IReporteBuilder(ABC):
    # PASOS INDISPENSABLES PARA ARMAR UN REPORTE FINANCIERO.

    @abstractmethod
    def reset(self, reporte_inicial: Any | None = None) -> None:
        # REINICIA LA CONSTRUCCION DESDE UNA PLANTILLA.
        pass

    @abstractmethod
    def definir_encabezado(self, titulo: str, periodo: str) -> None:
        # COLOCA EL TITULO Y EL PERIODO DEL REPORTE.
        pass

    @abstractmethod
    def construir_cuerpo_consolidado(self, secciones: Any) -> None:
        # ASIGNA LA ESTRUCTURA JERARQUICA DEL REPORTE.
        pass

    @abstractmethod
    def agregar_graficos(self, graficos: list[str]) -> None:
        # AGREGA LAS DESCRIPCIONES DE LOS GRAFICOS REQUERIDOS.
        pass

    @abstractmethod
    def agregar_conclusiones(self, conclusiones: list[str]) -> None:
        # AGREGA LAS CONCLUSIONES FINANCIERAS DEL PERIODO.
        pass

    @abstractmethod
    def agregar_totales(self) -> None:
        # CALCULA Y GUARDA EL TOTAL EN EUR.
        pass

    @abstractmethod
    def obtener_resultado(self) -> IReporteFinanciero:
        # ENTREGA EL REPORTE TERMINADO.
        pass

