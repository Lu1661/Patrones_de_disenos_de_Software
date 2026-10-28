# ENTIDAD QUE REPRESENTA UNA FILIAL COMERCIAL.

from dataclasses import dataclass

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

        if not isinstance(self.activa, bool):
            raise ValueError("El estado de la filial debe ser verdadero o falso.")

