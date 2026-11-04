# ENTIDAD QUE REPRESENTA UNA FILIAL COMERCIAL.

from dataclasses import dataclass
import re

from aplicacion.dominio.validaciones import (
    limpiar_texto,
    normalizar_codigo_iso,
    validar_id_opcional,
)


@dataclass
class Filial:
    # SEDE COMERCIAL QUE VENDE UTILIZANDO UNA DIVISA LOCAL.

    codigo: str
    nombre: str
    pais: str
    ciudad: str
    codigo_divisa: str
    activa: bool = True
    id_filial: int | None = None
    serie_factura: str | None = None
    ultimo_correlativo_factura: int = 0

    def __post_init__(self) -> None:
        # ============================================================
        # BLOQUE: VALIDACION DE UNA FILIAL
        # Este bloque identifica la sede y la moneda que utilizara en
        # sus ventas antes de permitir su ingreso al sistema.
        # Cumple: CU-05.
        # ============================================================
        self.codigo = limpiar_texto(self.codigo, "codigo de filial").upper()
        self.nombre = limpiar_texto(self.nombre, "nombre de filial")
        self.pais = limpiar_texto(self.pais, "pais")
        self.ciudad = limpiar_texto(self.ciudad, "ciudad")
        self.codigo_divisa = normalizar_codigo_iso(self.codigo_divisa)
        self.id_filial = validar_id_opcional(self.id_filial, "id de filial")
        if self.serie_factura is not None:
            self.serie_factura = limpiar_texto(
                self.serie_factura,
                "serie de factura",
            ).upper()
            if not re.fullmatch(r"F[0-9]{3}", self.serie_factura):
                raise ValueError("La serie de factura debe tener el formato F001.")
        if (
            isinstance(self.ultimo_correlativo_factura, bool)
            or not isinstance(self.ultimo_correlativo_factura, int)
            or self.ultimo_correlativo_factura < 0
            or self.ultimo_correlativo_factura > 999999
        ):
            raise ValueError("El correlativo de factura debe estar entre 0 y 999999.")

        if not isinstance(self.activa, bool):
            raise ValueError("El estado de la filial debe ser verdadero o falso.")

