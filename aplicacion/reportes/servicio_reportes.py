# COORDINACION FUNCIONAL DE LA GENERACION DE REPORTES.

from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from aplicacion.dominio.validaciones import redondear_moneda
from aplicacion.persistencia.repositorios.repositorio_filiales import (
    RepositorioFiliales,
)
from aplicacion.persistencia.repositorios.repositorio_productos import (
    RepositorioProductos,
)
from aplicacion.persistencia.repositorios.repositorio_ventas import (
    RepositorioVentas,
)
from aplicacion.reportes.estructura_reporte import (
    RegistroVentaHoja,
    SeccionCompuesta,
)
from aplicacion.servicios.fachada_serf import FachadaSERF
from aplicacion.servicios.utilidades import convertir_entero, obtener_requerido


MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


class ServicioReportes:
    # BUSCA LOS DATOS Y DELEGA A LA FACHADA LA CREACION DEL REPORTE.

    def __init__(
        self,
        repositorio_ventas: RepositorioVentas,
        repositorio_filiales: RepositorioFiliales,
        repositorio_productos: RepositorioProductos,
        fachada: FachadaSERF,
    ) -> None:
        self._repositorio_ventas = repositorio_ventas
        self._repositorio_filiales = repositorio_filiales
        self._repositorio_productos = repositorio_productos
        self._fachada = fachada

    def generar(self, datos: dict) -> dict:
        # GENERA UN REPORTE FINANCIERO LISTO PARA MOSTRAR E IMPRIMIR.

        # ============================================================
        # BLOQUE: PREPARACION DEL REPORTE FINANCIERO
        # Este bloque calcula el periodo, consulta las ventas y organiza
        # sus datos antes de entregarlos a los patrones de reportes.
        # Cumple: RF-05, RF-06, RF-07, RF-08, RF-09 y CU-06 a CU-09.
        # ============================================================
        tipo = str(obtener_requerido(datos, "tipo")).strip().lower()
        anio = convertir_entero(obtener_requerido(datos, "anio"), "anio")
        fecha_inicio, fecha_fin, periodo = self._calcular_periodo(
            tipo,
            anio,
            datos,
        )
        id_filial = self._obtener_filial_opcional(datos.get("id_filial"))
        filiales = self._repositorio_filiales.listar()
        productos = self._repositorio_productos.listar()
        mapa_filiales = {filial.id_filial: filial for filial in filiales}
        mapa_productos = {producto.id_producto: producto for producto in productos}

        filial_seleccionada = None
        if id_filial is not None:
            filial_seleccionada = mapa_filiales.get(id_filial)
            if filial_seleccionada is None:
                raise ValueError("La filial seleccionada no existe.")

        ventas = self._repositorio_ventas.listar_por_periodo(
            fecha_inicio,
            fecha_fin,
            id_filial,
        )
        estructura = self._construir_estructura(
            ventas,
            mapa_filiales,
            mapa_productos,
            filial_seleccionada,
        )
        totales = self._calcular_totales(ventas)
        comparativo = self._crear_comparativo(ventas, mapa_filiales)
        conclusiones = self._crear_conclusiones(totales, comparativo)
        graficos = [
            f"{item['filial']}: {item['total_eur']} EUR"
            for item in comparativo
        ] or ["Periodo sin ventas para comparar"]

        con_marca = self._convertir_booleano(datos.get("con_marca_agua", False))
        con_firma = self._convertir_booleano(datos.get("con_firma", False))
        contenido = self._fachada.emitir_reporte_consolidado(
            tipo,
            periodo,
            estructura,
            con_marca_agua=con_marca,
            con_firma=con_firma,
            graficos=graficos,
            conclusiones=conclusiones,
        )

        return {
            "tipo": tipo,
            "titulo": self._obtener_titulo(tipo),
            "periodo": periodo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_generacion": datetime.now().astimezone(),
            "alcance": (
                filial_seleccionada.nombre
                if filial_seleccionada
                else "Consolidado corporativo"
            ),
            "cantidad_ventas": len(ventas),
            **totales,
            "comparativo_filiales": comparativo,
            "ventas": self._preparar_ventas(ventas, mapa_filiales, mapa_productos),
            "contenido_emitido": contenido,
            "con_marca_agua": con_marca,
            "firma": self._extraer_firma(contenido) if con_firma else None,
        }

    @staticmethod
    def _calcular_periodo(
        tipo: str,
        anio: int,
        datos: dict,
    ) -> tuple[date, date, str]:
        # CONVIERTE EL TIPO SELECCIONADO EN FECHAS DE CONSULTA.

        hoy = date.today()
        if anio < 2000 or anio > hoy.year:
            raise ValueError(f"El año debe estar entre 2000 y {hoy.year}.")

        if tipo == "mensual":
            mes = convertir_entero(obtener_requerido(datos, "mes"), "mes")
            if mes > 12:
                raise ValueError("El mes debe estar entre 1 y 12.")
            inicio = date(anio, mes, 1)
            fin = date(anio, mes, monthrange(anio, mes)[1])
            periodo = f"{MESES[mes - 1].capitalize()} {anio}"
        elif tipo == "trimestral":
            trimestre = convertir_entero(
                obtener_requerido(datos, "trimestre"),
                "trimestre",
            )
            if trimestre > 4:
                raise ValueError("El trimestre debe estar entre 1 y 4.")
            mes_inicio = ((trimestre - 1) * 3) + 1
            mes_fin = mes_inicio + 2
            inicio = date(anio, mes_inicio, 1)
            fin = date(anio, mes_fin, monthrange(anio, mes_fin)[1])
            periodo = f"Trimestre {trimestre} de {anio}"
        elif tipo == "anual":
            inicio = date(anio, 1, 1)
            fin = date(anio, 12, 31)
            periodo = f"Año {anio}"
        else:
            raise ValueError("El tipo de reporte debe ser: mensual, trimestral o anual.")

        if inicio > hoy:
            raise ValueError("No se puede generar un reporte de un periodo futuro.")
        return inicio, min(fin, hoy), periodo

    @staticmethod
    def _obtener_filial_opcional(valor) -> int | None:
        if valor in (None, ""):
            return None
        return convertir_entero(valor, "id_filial")

    @staticmethod
    def _convertir_booleano(valor) -> bool:
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, str):
            valor_normalizado = valor.strip().lower()
            if valor_normalizado in ("true", "1", "si", "on"):
                return True
            if valor_normalizado in ("false", "0", "no", "", "off"):
                return False
        raise ValueError("Las opciones del reporte deben ser verdaderas o falsas.")

    @staticmethod
    def _obtener_titulo(tipo: str) -> str:
        return {
            "mensual": "Reporte mensual de ingresos",
            "trimestral": "Reporte trimestral de gastos e ingresos",
            "anual": "Reporte anual consolidado",
        }[tipo]

    @staticmethod
    def _construir_estructura(
        ventas,
        mapa_filiales: dict,
        mapa_productos: dict,
        filial_seleccionada,
    ) -> SeccionCompuesta:
        # FORMA EL ARBOL PAIS, FILIAL, CATEGORIA Y VENTA DEL COMPOSITE.

        nombre_raiz = (
            filial_seleccionada.nombre
            if filial_seleccionada
            else "Consolidado corporativo"
        )
        raiz = SeccionCompuesta(nombre_raiz)
        paises: dict[str, tuple[SeccionCompuesta, dict]] = {}

        for venta in ventas:
            filial = mapa_filiales.get(venta.id_filial)
            pais = filial.pais if filial else "Pais no identificado"
            nombre_filial = filial.nombre if filial else f"Filial {venta.id_filial}"
            if pais not in paises:
                seccion_pais = SeccionCompuesta(pais)
                raiz.agregar(seccion_pais)
                paises[pais] = (seccion_pais, {})
            seccion_pais, secciones_filial = paises[pais]
            if venta.id_filial not in secciones_filial:
                seccion_filial = SeccionCompuesta(nombre_filial)
                seccion_pais.agregar(seccion_filial)
                secciones_filial[venta.id_filial] = (seccion_filial, {})
            seccion_filial, categorias = secciones_filial[venta.id_filial]

            for detalle in venta.detalles:
                producto = mapa_productos.get(detalle.id_producto)
                categoria = producto.categoria if producto else "Sin categoria"
                if categoria not in categorias:
                    seccion_categoria = SeccionCompuesta(categoria)
                    seccion_filial.agregar(seccion_categoria)
                    categorias[categoria] = seccion_categoria
                nombre_producto = producto.nombre if producto else "Producto"
                categorias[categoria].agregar(
                    RegistroVentaHoja(
                        nombre=f"{venta.numero_factura} - {nombre_producto}",
                        subtotal_local=detalle.subtotal_local,
                        tasa_eur=venta.tasa_eur_aplicada,
                        codigo_divisa=venta.codigo_divisa,
                    )
                )
        return raiz

    @staticmethod
    def _calcular_totales(ventas) -> dict:
        ingresos = redondear_moneda(
            sum((venta.total_eur for venta in ventas), Decimal("0"))
        )
        gastos = redondear_moneda(
            sum((venta.total_costo_eur for venta in ventas), Decimal("0"))
        )
        return {
            "total_ingresos_eur": ingresos,
            "total_gastos_eur": gastos,
            "resultado_financiero_eur": redondear_moneda(ingresos - gastos),
        }

    @staticmethod
    def _crear_comparativo(ventas, mapa_filiales: dict) -> list[dict]:
        totales: dict[int, Decimal] = {}
        for venta in ventas:
            totales[venta.id_filial] = totales.get(
                venta.id_filial,
                Decimal("0"),
            ) + venta.total_eur
        resultado = []
        for id_filial, total in sorted(
            totales.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            filial = mapa_filiales.get(id_filial)
            resultado.append(
                {
                    "id_filial": id_filial,
                    "filial": filial.nombre if filial else f"Filial {id_filial}",
                    "total_eur": redondear_moneda(total),
                }
            )
        return resultado

    @staticmethod
    def _crear_conclusiones(totales: dict, comparativo: list[dict]) -> list[str]:
        ingresos = totales["total_ingresos_eur"]
        gastos = totales["total_gastos_eur"]
        resultado = totales["resultado_financiero_eur"]
        conclusiones = [
            f"Ingresos del periodo: {ingresos} EUR.",
            f"Gastos de importacion: {gastos} EUR.",
            f"Resultado financiero: {resultado} EUR.",
        ]
        if ingresos == Decimal("0.00"):
            conclusiones.append("El periodo no registra movimientos de venta.")
        elif resultado >= 0:
            conclusiones.append("El periodo presenta un resultado financiero positivo.")
        else:
            conclusiones.append("El periodo presenta un resultado financiero negativo.")
        if comparativo:
            conclusiones.append(
                f"La filial con mayores ingresos es {comparativo[0]['filial']}."
            )
        return conclusiones

    @staticmethod
    def _preparar_ventas(ventas, mapa_filiales: dict, mapa_productos: dict) -> list[dict]:
        filas = []
        for venta in ventas:
            filial = mapa_filiales.get(venta.id_filial)
            for detalle in venta.detalles:
                producto = mapa_productos.get(detalle.id_producto)
                filas.append(
                    {
                        "numero_factura": venta.numero_factura,
                        "fecha_venta": venta.fecha_venta,
                        "filial": filial.nombre if filial else str(venta.id_filial),
                        "producto": producto.nombre if producto else str(detalle.id_producto),
                        "categoria": producto.categoria if producto else "Sin categoria",
                        "cantidad": detalle.cantidad,
                        "total_local": detalle.subtotal_local,
                        "codigo_divisa": venta.codigo_divisa,
                        "total_eur": redondear_moneda(
                            detalle.subtotal_local * venta.tasa_eur_aplicada
                        ),
                        "gasto_eur": detalle.subtotal_costo_eur,
                    }
                )
        filas.sort(
            key=lambda fila: (
                fila["filial"].casefold(),
                fila["categoria"].casefold(),
                -fila["total_local"],
                fila["fecha_venta"],
            )
        )
        return filas

    @staticmethod
    def _extraer_firma(contenido: str) -> dict | None:
        # BUSCA LOS DATOS VISIBLES AGREGADOS POR EL DECORATOR DE FIRMA.

        campos = {}
        nombres = {
            "Emisor": "emisor",
            "Fecha": "fecha",
            "Identificador": "identificador",
            "SHA-256": "sha256",
        }
        for linea in contenido.splitlines():
            for etiqueta, clave in nombres.items():
                if linea.startswith(f"{etiqueta}:"):
                    campos[clave] = linea.split(":", 1)[1].strip()
        return campos or None

