# ENTIDAD QUE REPRESENTA UNA MONEDA UTILIZADA POR SERF.

from dataclasses import dataclass

from aplicacion.dominio.validaciones import limpiar_texto, normalizar_codigo_iso


@dataclass
class Divisa:
    # MONEDA DISPONIBLE PARA IMPORTACIONES, VENTAS Y REPORTES.

    codigo_iso: str
    nombre: str
    simbolo: str
    activa: bool = True

    def __post_init__(self) -> None:
        # ============================================================
        # BLOQUE: VALIDACION DE UNA DIVISA
        # Este bloque asegura que toda moneda tenga un codigo ISO de
        # tres letras y datos visibles antes de usarla en el sistema.
        # Cumple: RF-04 y CU-04.
        # ============================================================
        self.codigo_iso = normalizar_codigo_iso(self.codigo_iso)
        self.nombre = limpiar_texto(self.nombre, "nombre de divisa")
        self.simbolo = limpiar_texto(self.simbolo, "simbolo de divisa")

        if not isinstance(self.activa, bool):
            raise ValueError("El estado de la divisa debe ser verdadero o falso.")

