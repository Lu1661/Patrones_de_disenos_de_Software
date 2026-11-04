# ENTIDAD QUE REPRESENTA UNA CATEGORIA DEL CATALOGO.

from dataclasses import dataclass

from aplicacion.dominio.validaciones import limpiar_texto, validar_id_opcional


@dataclass
class CategoriaProducto:
    # CLASIFICACION ADMINISTRABLE PARA LOS PRODUCTOS IMPORTADOS.

    nombre: str
    activa: bool = True
    id_categoria: int | None = None

    def __post_init__(self) -> None:
        self.nombre = limpiar_texto(self.nombre, "nombre de categoria")
        if len(self.nombre) > 50:
            raise ValueError("El nombre de la categoria no puede superar 50 caracteres.")
        self.id_categoria = validar_id_opcional(
            self.id_categoria,
            "id de categoria",
        )
        if not isinstance(self.activa, bool):
            raise ValueError("El estado de la categoria debe ser verdadero o falso.")
