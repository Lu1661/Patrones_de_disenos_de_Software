# PERSISTENCIA DE FILIALES.

from mysql.connector.abstracts import MySQLConnectionAbstract

from aplicacion.dominio.contratos.contrato_repositorio import IRepositorioConsulta
from aplicacion.dominio.entidades.filial import Filial
from aplicacion.persistencia.conexion.conexion_mysql import ConexionMySQL
from aplicacion.persistencia.repositorios.repositorio_base import RepositorioBase


class RepositorioFiliales(RepositorioBase, IRepositorioConsulta[Filial]):
    # GUARDA Y CONSULTA LAS SEDES COMERCIALES DE FINANCORP.

    def __init__(self, administrador_conexion: ConexionMySQL) -> None:
        super().__init__(administrador_conexion)

    @staticmethod
    def _convertir_fila(fila: dict) -> Filial:
        return Filial(
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            pais=fila["pais"],
            ciudad=fila["ciudad"],
            codigo_divisa=fila["codigo_divisa"],
            activa=bool(fila["activa"]),
            id_filial=fila["id_filial"],
            serie_factura=fila["serie_factura"],
            ultimo_correlativo_factura=fila["ultimo_correlativo_factura"],
        )

    def listar(self) -> list[Filial]:
        # LISTA TODAS LAS FILIALES ORDENADAS POR NOMBRE.

        consulta = """
            SELECT id_filial, codigo, nombre, pais, ciudad,
                   codigo_divisa, activa, serie_factura,
                   ultimo_correlativo_factura
            FROM filiales
            ORDER BY nombre
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta)
                return [self._convertir_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    def listar_activas(self) -> list[Filial]:
        # LISTA LAS FILIALES HABILITADAS PARA REGISTRAR OPERACIONES.

        return [filial for filial in self.listar() if filial.activa]

    def obtener_por_id(self, identificador: int) -> Filial | None:
        # BUSCA UNA FILIAL POR SU CLAVE PRIMARIA.

        consulta = """
            SELECT id_filial, codigo, nombre, pais, ciudad,
                   codigo_divisa, activa, serie_factura,
                   ultimo_correlativo_factura
            FROM filiales
            WHERE id_filial = %s
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (identificador,))
                fila = cursor.fetchone()
                return self._convertir_fila(fila) if fila else None
            finally:
                cursor.close()

    def crear(
        self,
        filial: Filial,
        conexion: MySQLConnectionAbstract | None = None,
    ) -> int:
        # INSERTA UNA FILIAL Y DEVUELVE SU IDENTIFICADOR.

        consulta = """
            INSERT INTO filiales
                (codigo, nombre, pais, ciudad, codigo_divisa, activa,
                 serie_factura, ultimo_correlativo_factura)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        parametros = (
            filial.codigo,
            filial.nombre,
            filial.pais,
            filial.ciudad,
            filial.codigo_divisa,
            filial.activa,
            filial.serie_factura,
            filial.ultimo_correlativo_factura,
        )
        with self._usar_conexion(conexion, escritura=True) as conexion_actual:
            cursor = conexion_actual.cursor()
            try:
                cursor.execute(consulta, parametros)
                filial.id_filial = cursor.lastrowid
                return cursor.lastrowid
            finally:
                cursor.close()

    def obtener_siguiente_serie(self) -> str:
        # CALCULA LA SERIE QUE LE CORRESPONDE A UNA NUEVA FILIAL.

        consulta = """
            SELECT COALESCE(MAX(CAST(SUBSTRING(serie_factura, 2) AS UNSIGNED)), 0)
                   AS ultima_serie
            FROM filiales
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta)
                siguiente = int(cursor.fetchone()["ultima_serie"]) + 1
            finally:
                cursor.close()
        if siguiente > 999:
            raise ValueError("No existen mas series disponibles para filiales.")
        return f"F{siguiente:03d}"

    def previsualizar_siguiente_factura(self, id_filial: int) -> str:
        # MUESTRA EL SIGUIENTE NUMERO SIN RESERVARLO TODAVIA.

        consulta = """
            SELECT serie_factura, ultimo_correlativo_factura
            FROM filiales
            WHERE id_filial = %s AND activa = TRUE
        """
        with self._usar_conexion() as conexion:
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute(consulta, (id_filial,))
                fila = cursor.fetchone()
            finally:
                cursor.close()
        if fila is None:
            raise ValueError("La filial indicada no existe o esta inactiva.")
        siguiente = int(fila["ultimo_correlativo_factura"]) + 1
        if siguiente > 999999:
            raise ValueError("La filial alcanzo el limite de facturas permitido.")
        return f"{fila['serie_factura']}-{siguiente:06d}"

    def reservar_siguiente_factura(
        self,
        id_filial: int,
        conexion: MySQLConnectionAbstract,
    ) -> str:
        # RESERVA EL CORRELATIVO DENTRO DE LA MISMA TRANSACCION DE LA VENTA.

        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT serie_factura, ultimo_correlativo_factura
                FROM filiales
                WHERE id_filial = %s AND activa = TRUE
                FOR UPDATE
                """,
                (id_filial,),
            )
            fila = cursor.fetchone()
            if fila is None:
                raise ValueError("La filial indicada no existe o esta inactiva.")
            siguiente = int(fila["ultimo_correlativo_factura"]) + 1
            if siguiente > 999999:
                raise ValueError("La filial alcanzo el limite de facturas permitido.")
            cursor.execute(
                """
                UPDATE filiales
                SET ultimo_correlativo_factura = %s
                WHERE id_filial = %s
                """,
                (siguiente, id_filial),
            )
            return f"{fila['serie_factura']}-{siguiente:06d}"
        finally:
            cursor.close()

    def actualizar(self, filial: Filial) -> None:
        # ACTUALIZA LOS DATOS ADMINISTRATIVOS DE UNA FILIAL EXISTENTE.

        consulta = """
            UPDATE filiales
            SET codigo = %s, nombre = %s, pais = %s, ciudad = %s,
                codigo_divisa = %s
            WHERE id_filial = %s
        """
        parametros = (
            filial.codigo,
            filial.nombre,
            filial.pais,
            filial.ciudad,
            filial.codigo_divisa,
            filial.id_filial,
        )
        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(consulta, parametros)
            finally:
                cursor.close()

    def desactivar(self, id_filial: int) -> None:
        # MARCA UNA FILIAL COMO INACTIVA SIN BORRAR SU HISTORIAL.

        with self._usar_conexion(escritura=True) as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(
                    "UPDATE filiales SET activa = FALSE "
                    "WHERE id_filial = %s AND activa = TRUE",
                    (id_filial,),
                )
                if cursor.rowcount == 0:
                    raise ValueError("La filial indicada no existe o ya esta inactiva.")
            finally:
                cursor.close()

