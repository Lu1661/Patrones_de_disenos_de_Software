"""Validaciones sencillas compartidas por las entidades del dominio."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


DOS_DECIMALES = Decimal("0.01")
OCHO_DECIMALES = Decimal("0.00000001")


def limpiar_texto(valor: str, campo: str) -> str:
    """Retorna un texto sin espacios sobrantes o informa el campo invalido."""

    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"El campo {campo} es obligatorio.")
    return valor.strip()


def normalizar_codigo_iso(valor: str) -> str:
    """Valida y normaliza un codigo ISO de moneda de tres letras."""

    codigo = limpiar_texto(valor, "codigo de divisa").upper()
    if not re.fullmatch(r"[A-Z]{3}", codigo):
        raise ValueError("El codigo de divisa debe contener tres letras.")
    return codigo


def convertir_decimal(valor: Decimal | str | int, campo: str) -> Decimal:
    """Convierte un valor numerico a Decimal sin utilizar calculos con float."""

    if isinstance(valor, (bool, float)):
        raise ValueError(
            f"El campo {campo} debe recibirse como Decimal, texto o entero."
        )

    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"El campo {campo} debe ser numerico.") from error

    if not numero.is_finite():
        raise ValueError(f"El campo {campo} debe ser un numero finito.")
    return numero


def validar_decimal_positivo(valor: Decimal | str | int, campo: str) -> Decimal:
    """Valida un importe estrictamente mayor que cero."""

    numero = convertir_decimal(valor, campo)
    if numero <= 0:
        raise ValueError(f"El campo {campo} debe ser mayor que cero.")
    return numero


def validar_decimal_no_negativo(
    valor: Decimal | str | int,
    campo: str,
) -> Decimal:
    """Valida un importe que puede ser cero, pero nunca negativo."""

    numero = convertir_decimal(valor, campo)
    if numero < 0:
        raise ValueError(f"El campo {campo} no puede ser negativo.")
    return numero


def redondear_moneda(valor: Decimal | str | int) -> Decimal:
    """Aplica el redondeo monetario definido para importes visibles."""

    return convertir_decimal(valor, "importe").quantize(
        DOS_DECIMALES,
        rounding=ROUND_HALF_UP,
    )


def redondear_tasa(valor: Decimal | str | int) -> Decimal:
    """Conserva la precision de ocho decimales de una tasa de cambio."""

    return validar_decimal_positivo(valor, "tasa").quantize(
        OCHO_DECIMALES,
        rounding=ROUND_HALF_UP,
    )


def validar_entero_positivo(valor: int, campo: str) -> int:
    """Valida identificadores y cantidades mayores que cero."""

    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"El campo {campo} debe ser un entero mayor que cero.")
    return valor


def validar_entero_no_negativo(valor: int, campo: str) -> int:
    """Valida existencias que pueden ser cero, pero nunca negativas."""

    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ValueError(f"El campo {campo} debe ser un entero no negativo.")
    return valor


def validar_id_opcional(valor: int | None, campo: str) -> int | None:
    """Permite una entidad nueva sin id y valida un id ya asignado."""

    if valor is None:
        return None
    return validar_entero_positivo(valor, campo)


def validar_fecha_no_futura(valor: date | datetime, campo: str) -> date | datetime:
    """Impide registrar importaciones o ventas con una fecha futura."""

    if not isinstance(valor, (date, datetime)):
        raise ValueError(f"El campo {campo} debe ser una fecha valida.")

    fecha_comparable = valor.date() if isinstance(valor, datetime) else valor
    if fecha_comparable > date.today():
        raise ValueError(f"El campo {campo} no puede ser una fecha futura.")
    return valor

