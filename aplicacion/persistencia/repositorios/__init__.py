# REPOSITORIOS CONCRETOS PARA GUARDAR Y CONSULTAR INFORMACION.

from aplicacion.persistencia.repositorios.repositorio_filiales import (
    RepositorioFiliales,
)
from aplicacion.persistencia.repositorios.repositorio_inventario import (
    RepositorioInventario,
)
from aplicacion.persistencia.repositorios.repositorio_productos import (
    RepositorioProductos,
)
from aplicacion.persistencia.repositorios.repositorio_tipos_cambio import (
    RepositorioTiposCambio,
)
from aplicacion.persistencia.repositorios.repositorio_ventas import (
    RepositorioVentas,
)


__all__ = [
    "RepositorioFiliales",
    "RepositorioInventario",
    "RepositorioProductos",
    "RepositorioTiposCambio",
    "RepositorioVentas",
]

