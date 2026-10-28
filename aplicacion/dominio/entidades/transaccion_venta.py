# ENTIDAD QUE REPRESENTA LA CABECERA DE UNA VENTA.

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal

from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.validaciones import (
    limpiar_texto,
    normalizar_codigo_iso,
    redondear_moneda,
    redondear_tasa,
    validar_entero_positivo,
    validar_fecha_no_futura,
    validar_id_opcional,
)


METODOS_PAGO_PERMITIDOS = ("Efectivo", "Tarjeta", "Transferencia")


@dataclass
class TransaccionVenta:
    # COMPROBANTE DE VENTA REALIZADO EN LA DIVISA LOCAL DE UNA FILIAL.

    numero_factura: str
    id_filial: int
    fecha_venta: datetime | date
    cliente: str
    vendedor: str
    metodo_pago: str
    codigo_divisa: str
    tasa_eur_aplicada: Decimal
    detalles: list[DetalleVenta] = field(default_factory=list)
    id_venta: int | None = None

    def __post_init__(self) -> None:
        # ============================================================
        # BLOQUE: VALIDACION DE LA CABECERA DE VENTA
        # Este bloque normaliza el comprobante, su filial, moneda y
        # tasa historica antes de calcular los totales de la operacion.
        # Cumple: RF-02, RF-04 y CU-02.
        # ============================================================
        self.numero_factura = limpiar_texto(
            self.numero_factura,
            "numero de factura",
        ).upper()
        self.id_filial = validar_entero_positivo(self.id_filial, "id de filial")
        self.fecha_venta = validar_fecha_no_futura(
            self.fecha_venta,
            "fecha de venta",
        )
        if isinstance(self.fecha_venta, date) and not isinstance(
            self.fecha_venta,
            datetime,
        ):
            self.fecha_venta = datetime.combine(self.fecha_venta, time.min)

        self.cliente = limpiar_texto(self.cliente, "cliente")
        self.vendedor = limpiar_texto(self.vendedor, "vendedor")
        self.metodo_pago = self._normalizar_metodo_pago(self.metodo_pago)
        self.codigo_divisa = normalizar_codigo_iso(self.codigo_divisa)
        self.tasa_eur_aplicada = redondear_tasa(self.tasa_eur_aplicada)
        self.id_venta = validar_id_opcional(self.id_venta, "id de venta")

        detalles_recibidos = list(self.detalles)
        self.detalles = []
        for detalle in detalles_recibidos:
            self.agregar_detalle(detalle)

        if self.codigo_divisa == "EUR" and self.tasa_eur_aplicada != Decimal(
            "1.00000000"
        ):
            raise ValueError("La tasa de una venta en EUR debe ser igual a 1.")

    @staticmethod
    def _normalizar_metodo_pago(metodo_pago: str) -> str:
        # DEVUELVE LA ESCRITURA OFICIAL DE UN METODO DE PAGO PERMITIDO.

        valor = limpiar_texto(metodo_pago, "metodo de pago")
        for metodo_permitido in METODOS_PAGO_PERMITIDOS:
            if metodo_permitido.lower() == valor.lower():
                return metodo_permitido
        opciones = ", ".join(METODOS_PAGO_PERMITIDOS)
        raise ValueError(f"El metodo de pago debe ser: {opciones}.")

    def agregar_detalle(self, detalle: DetalleVenta) -> None:
        # AGREGA UN PRODUCTO VALIDO Y EVITA REPETIRLO EN EL COMPROBANTE.

        if not isinstance(detalle, DetalleVenta):
            raise ValueError("La venta solo puede contener detalles validos.")
        if any(
            existente.id_producto == detalle.id_producto
            for existente in self.detalles
        ):
            raise ValueError("El producto ya fue agregado a la venta.")
        self.detalles.append(detalle)

    def validar_para_registro(self) -> None:
        # COMPRUEBA QUE LA VENTA TENGA AL MENOS UN PRODUCTO ANTES DE GUARDARLA.

        if not self.detalles:
            raise ValueError("La venta debe contener al menos un producto.")

    @property
    def total_local(self) -> Decimal:
        # SUMA LOS SUBTOTALES EXPRESADOS EN LA MONEDA LOCAL.

        return redondear_moneda(
            sum((detalle.subtotal_local for detalle in self.detalles), Decimal("0"))
        )

    @property
    def total_eur(self) -> Decimal:
        # CONVIERTE EL TOTAL LOCAL A LA MONEDA CORPORATIVA EUR.

        return redondear_moneda(self.total_local * self.tasa_eur_aplicada)

    @property
    def total_costo_eur(self) -> Decimal:
        # SUMA LOS COSTOS HISTORICOS DE IMPORTACION DE LOS PRODUCTOS VENDIDOS.

        return redondear_moneda(
            sum(
                (detalle.subtotal_costo_eur for detalle in self.detalles),
                Decimal("0"),
            )
        )

    @property
    def resultado_financiero_eur(self) -> Decimal:
        # CALCULA INGRESOS MENOS GASTOS DE IMPORTACION PARA LA VENTA.

        return redondear_moneda(self.total_eur - self.total_costo_eur)

