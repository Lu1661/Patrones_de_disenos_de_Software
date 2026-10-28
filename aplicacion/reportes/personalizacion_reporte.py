# MARCA DE AGUA Y FIRMA ACADEMICA OPCIONALES DEL REPORTE.

from datetime import datetime
from hashlib import sha256

from aplicacion.dominio.contratos.contrato_reporte import IReporteFinanciero
from aplicacion.dominio.validaciones import limpiar_texto


class ReporteDecorator(IReporteFinanciero):
    # ENVOLTORIO BASE QUE DELEGA LA EMISION AL REPORTE RECIBIDO.

    def __init__(self, reporte_envuelto: IReporteFinanciero) -> None:
        if not isinstance(reporte_envuelto, IReporteFinanciero):
            raise ValueError("Solo se puede personalizar un reporte financiero.")
        self._reporte_envuelto = reporte_envuelto

    def emitir(self) -> str:
        # DELEGA LA GENERACION DEL CONTENIDO AL COMPONENTE ENVUELTO.

        return self._reporte_envuelto.emitir()


class MarcaDeAguaDecorator(ReporteDecorator):
    # AGREGA UNA MARCA DE AGUA TEXTUAL SIN CAMBIAR EL REPORTE BASE.

    def __init__(
        self,
        reporte_envuelto: IReporteFinanciero,
        texto: str = "CONFIDENCIAL - FINANCORP S.A.",
    ) -> None:
        super().__init__(reporte_envuelto)
        self._texto = limpiar_texto(texto, "marca de agua")

    def emitir(self) -> str:
        # ============================================================
        # PATRON DECORATOR: MARCA DE AGUA OPCIONAL
        # Este bloque agrega un sello visual sin modificar la clase del
        # reporte ni su informacion financiera original.
        # Cumple: RF-08 y CU-09.
        # ============================================================
        contenido = super().emitir()
        return f"[MARCA DE AGUA: {self._texto}]\n\n{contenido}"


class FirmaDigitalDecorator(ReporteDecorator):
    # AGREGA UNA DEMOSTRACION ACADEMICA DE INTEGRIDAD CON SHA-256.

    def __init__(
        self,
        reporte_envuelto: IReporteFinanciero,
        emisor: str = "FinanCorp S.A.",
    ) -> None:
        super().__init__(reporte_envuelto)
        self._emisor = limpiar_texto(emisor, "emisor de firma")

    def emitir(self) -> str:
        # ============================================================
        # PATRON DECORATOR: FIRMA DIGITAL ACADEMICA
        # Este bloque tiene el contenido contenido final y lo
        # adjunta como evidencia academica de integridad documental.
        # Cumple: RF-08 y CU-09.
        # ============================================================
        contenido = super().emitir()
        hash_documento = sha256(contenido.encode("utf-8")).hexdigest()
        fecha_firma = datetime.now().astimezone().isoformat(timespec="seconds")
        identificador = hash_documento[:16].upper()

        bloque_firma = "\n".join(
            [
                "",
                "FIRMA DIGITAL ACADEMICA",
                f"Emisor: {self._emisor}",
                f"Fecha: {fecha_firma}",
                f"Identificador: {identificador}",
                f"SHA-256: {hash_documento}",
            ]
        )
        return f"{contenido}\n{bloque_firma}"

