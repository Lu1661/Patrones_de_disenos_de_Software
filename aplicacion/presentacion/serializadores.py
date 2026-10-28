# CONVERSION DE ENTIDADES DEL DOMINIO A VALORES COMPATIBLES CON JSON.

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal


def serializar(valor):
    # CONVIERTE RECURSIVAMENTE FECHAS, DECIMALES Y ENTIDADES PARA LA API.

    if isinstance(valor, Decimal):
        return format(valor, "f")
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if is_dataclass(valor) and not isinstance(valor, type):
        resultado = {
            campo.name: serializar(getattr(valor, campo.name))
            for campo in fields(valor)
        }

        # ============================================================
        # BLOQUE: TOTALES CALCULADOS PARA LA RESPUESTA JSON
        # Estos valores no se guardan dos veces en las entidades, pero
        # el frontend los necesita para mostrar importes y resultados.
        # ============================================================
        propiedades_calculadas = (
            "subtotal_local",
            "subtotal_costo_eur",
            "total_local",
            "total_eur",
            "total_costo_eur",
            "resultado_financiero_eur",
        )
        for nombre in propiedades_calculadas:
            if isinstance(getattr(type(valor), nombre, None), property):
                resultado[nombre] = serializar(getattr(valor, nombre))
        return resultado
    if isinstance(valor, dict):
        return {clave: serializar(contenido) for clave, contenido in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [serializar(contenido) for contenido in valor]
    return valor
