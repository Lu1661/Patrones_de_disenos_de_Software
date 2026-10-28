# CONVERSIONES SENCILLAS PARA LOS DATOS RECIBIDOS POR EL BACKEND.

from datetime import date, datetime


def obtener_requerido(datos: dict, campo: str) -> object:
    # BUSCA UN CAMPO OBLIGATORIO SIN ACEPTAR TEXTOS VACIOS.

    valor = datos.get(campo)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        raise ValueError(f"El campo {campo} es obligatorio.")
    return valor


def convertir_entero(valor: object, campo: str) -> int:
    # CONVIERTE UN DATO DE FORMULARIO EN UN ENTERO VALIDO.

    if isinstance(valor, bool):
        raise ValueError(f"El campo {campo} debe ser un numero entero.")
    try:
        return int(str(valor))
    except (TypeError, ValueError) as error:
        raise ValueError(f"El campo {campo} debe ser un numero entero.") from error


def convertir_fecha(valor: object, campo: str) -> date:
    # CONVIERTE UNA FECHA ISO CON FORMATO AAAA-MM-DD.

    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor))
    except (TypeError, ValueError) as error:
        raise ValueError(f"El campo {campo} debe usar el formato AAAA-MM-DD.") from error


def convertir_fecha_hora(valor: object, campo: str) -> datetime:
    # CONVIERTE UNA FECHA O FECHA-HORA ISO PARA REGISTRAR UNA VENTA.

    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time())

    texto = str(valor)
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(texto), datetime.min.time())
        except ValueError as error:
            raise ValueError(
                f"El campo {campo} debe contener una fecha ISO valida."
            ) from error
