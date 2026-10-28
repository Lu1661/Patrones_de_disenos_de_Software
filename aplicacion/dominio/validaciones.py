# VALIDACIONES SENCILLAS COMPARTIDAS POR LAS ENTIDADES DEL DOMINIO.

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


DOS_DECIMALES = Decimal("0.01")
OCHO_DECIMALES = Decimal("0.00000001")


def limpiar_texto(valor: str, campo: str) -> str:
    # DEVUELVE UN TEXTO SIN ESPACIOS SOBRANTES O INFORMA EL CAMPO INVALIDO.

    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"El campo {campo} es obligatorio.")
    return valor.strip()


def normalizar_codigo_iso(valor: str) -> str:
    # VALIDA Y NORMALIZA UN CODIGO ISO DE MONEDA DE TRES LETRAS.

    codigo = limpiar_texto(valor, "codigo de divisa").upper()
    if not re.fullmatch(r"[A-Z]{3}", codigo):
        raise ValueError("El codigo de divisa debe contener tres letras.")
    return codigo


def convertir_decimal(valor: Decimal | str | int, campo: str) -> Decimal:
    # CONVIERTE UN VALOR NUMERICO A DECIMAL SIN UTILIZAR CALCULOS CON FLOAT.

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
    # VALIDA UN IMPORTE ESTRICTAMENTE MAYOR QUE CERO.

    numero = convertir_decimal(valor, campo)
    if numero <= 0:
        raise ValueError(f"El campo {campo} debe ser mayor que cero.")
    return numero


def validar_decimal_no_negativo(
    valor: Decimal | str | int,
    campo: str,
) -> Decimal:
    # VALIDA UN IMPORTE QUE PUEDE SER CERO, PERO NUNCA NEGATIVO.

    numero = convertir_decimal(valor, campo)
    if numero < 0:
        raise ValueError(f"El campo {campo} no puede ser negativo.")
    return numero


def redondear_moneda(valor: Decimal | str | int) -> Decimal:
    # APLICA EL REDONDEO MONETARIO DEFINIDO PARA IMPORTES VISIBLES.

    return convertir_decimal(valor, "importe").quantize(
        DOS_DECIMALES,
        rounding=ROUND_HALF_UP,
    )


def redondear_tasa(valor: Decimal | str | int) -> Decimal:
    # GUARDA LA PRECISION DE OCHO DECIMALES DE UNA TASA DE CAMBIO.

    return validar_decimal_positivo(valor, "tasa").quantize(
        OCHO_DECIMALES,
        rounding=ROUND_HALF_UP,
    )


def validar_entero_positivo(valor: int, campo: str) -> int:
    # VALIDA IDENTIFICADORES Y CANTIDADES MAYORES QUE CERO.

    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"El campo {campo} debe ser un entero mayor que cero.")
    return valor


def validar_entero_no_negativo(valor: int, campo: str) -> int:
    # VALIDA EXISTENCIAS QUE PUEDEN SER CERO, PERO NUNCA NEGATIVAS.

    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ValueError(f"El campo {campo} debe ser un entero no negativo.")
    return valor


def validar_id_opcional(valor: int | None, campo: str) -> int | None:
    # PERMITE UNA ENTIDAD NUEVA SIN ID Y VALIDA UN ID YA ASIGNADO.

    if valor is None:
        return None
    return validar_entero_positivo(valor, campo)


def validar_fecha_no_futura(valor: date | datetime, campo: str) -> date | datetime:
    # IMPIDE REGISTRAR IMPORTACIONES O VENTAS CON UNA FECHA FUTURA.

    if not isinstance(valor, (date, datetime)):
        raise ValueError(f"El campo {campo} debe ser una fecha valida.")

    fecha_comparable = valor.date() if isinstance(valor, datetime) else valor
    if fecha_comparable > date.today():
        raise ValueError(f"El campo {campo} no puede ser una fecha futura.")
    return valor

