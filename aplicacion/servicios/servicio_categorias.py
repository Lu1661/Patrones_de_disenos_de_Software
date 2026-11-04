# PROCESOS DE LAS CATEGORIAS DEL CATALOGO.

from aplicacion.dominio.entidades.categoria_producto import CategoriaProducto
from aplicacion.persistencia.repositorios.repositorio_categorias import (
    RepositorioCategorias,
)
from aplicacion.servicios.utilidades import obtener_requerido


class ServicioCategorias:
    # PERMITE CONSULTAR Y AGREGAR CATEGORIAS SIN CAMBIAR EL CODIGO HTML.

    def __init__(self, repositorio: RepositorioCategorias) -> None:
        self._repositorio = repositorio

    def listar(self) -> list[CategoriaProducto]:
        return self._repositorio.listar()

    def registrar(self, datos: dict) -> CategoriaProducto:
        categoria = CategoriaProducto(
            nombre=str(obtener_requerido(datos, "nombre")),
        )
        existente = self._repositorio.obtener_por_nombre(categoria.nombre)
        if existente is not None:
            raise ValueError("La categoria indicada ya se encuentra registrada.")
        self._repositorio.crear(categoria)
        return categoria

    def obtener_activa(self, nombre: str) -> CategoriaProducto:
        categoria = self._repositorio.obtener_por_nombre(nombre)
        if categoria is None or not categoria.activa:
            raise ValueError("La categoria indicada no existe o esta inactiva.")
        return categoria
