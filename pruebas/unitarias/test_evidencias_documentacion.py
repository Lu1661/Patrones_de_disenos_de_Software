from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from aplicacion.crear_aplicacion import crear_aplicacion
from aplicacion.dominio.entidades.detalle_venta import DetalleVenta
from aplicacion.dominio.entidades.filial import Filial
from aplicacion.dominio.entidades.inventario_filial import InventarioFilial
from aplicacion.dominio.entidades.producto_importado import ProductoImportado
from aplicacion.dominio.entidades.tipo_cambio import TipoCambio
from aplicacion.dominio.entidades.transaccion_venta import TransaccionVenta
from aplicacion.presentacion.controladores.controlador_autenticacion import (
    intentos_acceso,
)
from aplicacion.reportes.servicio_reportes import ServicioReportes
from aplicacion.servicios.fachada_serf import FachadaSERF
from aplicacion.servicios.servicio_categorias import ServicioCategorias
from aplicacion.servicios.servicio_inventario import ServicioInventario
from aplicacion.servicios.servicio_productos import ServicioProductos
from aplicacion.servicios.servicio_ventas import ServicioVentas


def configurar_aplicacion(monkeypatch):
    monkeypatch.setattr(
        "aplicacion.configuracion.configuracion_entorno.ConfiguracionEntorno.MYSQL_USUARIO",
        "",
    )
    monkeypatch.setattr(
        "aplicacion.configuracion.configuracion_entorno.ConfiguracionEntorno.MYSQL_PASSWORD",
        "",
    )
    aplicacion = crear_aplicacion()
    aplicacion.config.update(
        TESTING=True,
        ADMIN_USUARIO="admin",
        ADMIN_PASSWORD="clave-admin-prueba",
        SUPERVISOR_USUARIO="supervisor",
        SUPERVISOR_PASSWORD="clave-supervisor-prueba",
        VENDEDOR_USUARIO="vendedor",
        VENDEDOR_PASSWORD="clave-vendedor-prueba",
    )
    return aplicacion


def crear_servicio_productos(servicio_categorias):
    administrador = MagicMock()
    repositorio_productos = MagicMock()
    repositorio_inventario = MagicMock()
    repositorio_filiales = MagicMock()
    repositorio_tasas = MagicMock()
    repositorio_filiales.obtener_por_id.return_value = Filial(
        codigo="PE-LIM-01",
        nombre="Filial Lima",
        pais="Peru",
        ciudad="Lima",
        codigo_divisa="PEN",
        id_filial=1,
    )
    tasas = {
        "CNY": TipoCambio("CNY", "0.14000000", date.today()),
        "PEN": TipoCambio("PEN", "0.25000000", date.today()),
    }
    repositorio_tasas.obtener_vigente.side_effect = (
        lambda codigo, _fecha: tasas.get(codigo)
    )

    def asignar_id(producto, _conexion):
        producto.id_producto = 1

    repositorio_productos.crear.side_effect = asignar_id
    servicio = ServicioProductos(
        administrador,
        repositorio_productos,
        repositorio_inventario,
        repositorio_filiales,
        repositorio_tasas,
        servicio_categorias,
    )
    return servicio, repositorio_productos, repositorio_inventario


def datos_producto():
    return {
        "codigo": "LAP-001",
        "nombre": "Laptop de prueba",
        "descripcion_tecnica": "Equipo para comprobar el registro",
        "categoria": "Laptop",
        "costo_unitario_cny": "100.00",
        "proveedor": "Proveedor de prueba",
        "fecha_importacion": date.today().isoformat(),
        "id_filial": 1,
        "stock_inicial": 10,
    }


def test_01_inicio_de_sesion_bloqueo_y_roles(monkeypatch):
    intentos_acceso.clear()
    aplicacion = configurar_aplicacion(monkeypatch)

    visitante = aplicacion.test_client()
    estados = [
        visitante.post(
            "/login",
            data={"usuario": "cuenta-error", "password": "incorrecta"},
        ).status_code
        for _ in range(3)
    ]
    assert estados == [401, 401, 429]

    administrador = aplicacion.test_client()
    assert administrador.post(
        "/login",
        data={"usuario": "admin", "password": "clave-admin-prueba"},
    ).status_code == 302
    assert administrador.get("/configuracion").status_code == 200

    supervisor = aplicacion.test_client()
    assert supervisor.post(
        "/login",
        data={"usuario": "supervisor", "password": "clave-supervisor-prueba"},
    ).status_code == 302
    assert supervisor.get("/inventario").status_code == 200
    assert supervisor.get("/configuracion").status_code == 403

    vendedor = aplicacion.test_client()
    assert vendedor.post(
        "/login",
        data={"usuario": "vendedor", "password": "clave-vendedor-prueba"},
    ).status_code == 302
    assert vendedor.get("/productos").status_code == 200
    assert vendedor.get("/reportes").status_code == 403
    intentos_acceso.clear()


def test_02_conversion_de_monedas():
    tasa = TipoCambio("CNY", "0.13000000", date.today())
    assert tasa.convertir_a_eur("100.00") == Decimal("13.00")


def test_03_calculo_del_precio_de_venta():
    categorias = MagicMock()
    categorias.obtener_activa.return_value.nombre = "Laptop"
    servicio, _productos, inventarios = crear_servicio_productos(categorias)

    _producto, inventario = servicio.registrar_con_stock(datos_producto())

    assert inventario.precio_venta_local == Decimal("67.20")
    inventarios.crear.assert_called_once()


def test_04_registro_de_productos_y_categorias():
    repositorio_categorias = MagicMock()
    repositorio_categorias.obtener_por_nombre.return_value = None
    categorias = ServicioCategorias(repositorio_categorias)
    categoria = categorias.registrar({"nombre": "Laptop"})
    repositorio_categorias.obtener_por_nombre.return_value = categoria
    servicio, productos, _inventarios = crear_servicio_productos(categorias)

    producto, _inventario = servicio.registrar_con_stock(datos_producto())

    assert categoria.nombre == "Laptop"
    assert producto.codigo == "LAP-001"
    assert producto.categoria == "Laptop"
    repositorio_categorias.crear.assert_called_once_with(categoria)
    productos.crear.assert_called_once()


def test_05_estados_y_actualizacion_del_inventario():
    inventario = InventarioFilial(1, 1, 0, "67.20")
    repositorio = MagicMock()
    repositorio.obtener.return_value = inventario

    def reponer(_filial, _producto, cantidad):
        inventario.reponer_stock(cantidad)

    repositorio.reponer_stock.side_effect = reponer
    servicio = ServicioInventario(repositorio)

    assert inventario.stock_disponible == 0
    assert inventario.stock_disponible == 0
    servicio.reponer({"id_filial": 1, "id_producto": 1, "cantidad": 5})
    assert 1 <= inventario.stock_disponible <= 10
    servicio.reponer({"id_filial": 1, "id_producto": 1, "cantidad": 6})
    assert inventario.stock_disponible > 10


def test_06_registro_de_ventas_y_descuento_de_stock():
    administrador = MagicMock()
    conexion = object()
    administrador.transaccion.return_value.__enter__.return_value = conexion
    ventas = MagicMock()
    inventarios = MagicMock()
    productos = MagicMock()
    filiales = MagicMock()
    tasas = MagicMock()
    filial = Filial(
        codigo="PE-LIM-01",
        nombre="Filial Lima",
        pais="Peru",
        ciudad="Lima",
        codigo_divisa="PEN",
        id_filial=1,
        serie_factura="F001",
    )
    producto = ProductoImportado.crear_con_conversion(
        codigo="LAP-001",
        nombre="Laptop de prueba",
        descripcion_tecnica="Equipo para comprobar la venta",
        categoria="Laptop",
        costo_unitario_cny="100.00",
        tasa_cny_eur="0.13000000",
        proveedor="Proveedor de prueba",
        fecha_importacion=date.today(),
    )
    producto.id_producto = 1
    inventario = InventarioFilial(1, 1, 10, "67.20")
    filiales.obtener_por_id.return_value = filial
    filiales.reservar_siguiente_factura.return_value = "F001-000001"
    productos.obtener_por_id.return_value = producto
    inventarios.obtener.return_value = inventario
    tasas.obtener_vigente.return_value = TipoCambio(
        "PEN", "0.25000000", date.today()
    )

    def descontar(_filial, _producto, cantidad, _conexion):
        inventario.descontar_stock(cantidad)

    inventarios.descontar_stock.side_effect = descontar
    servicio = ServicioVentas(
        administrador,
        ventas,
        inventarios,
        productos,
        filiales,
        tasas,
    )

    venta = servicio.registrar(
        {
            "id_filial": 1,
            "id_producto": 1,
            "cantidad": 4,
            "fecha_venta": datetime.now().replace(microsecond=0).isoformat(),
            "cliente": "Cliente de prueba",
            "vendedor": "Vendedor de prueba",
            "metodo_pago": "Tarjeta",
        }
    )

    assert venta.numero_factura == "F001-000001"
    assert venta.detalles[0].cantidad == 4
    assert inventario.stock_disponible == 6
    ventas.registrar.assert_called_once_with(venta, conexion)


def test_07_generacion_y_filtros_de_reportes():
    filial_1 = Filial("PE-LIM-01", "Filial Lima", "Peru", "Lima", "PEN", id_filial=1)
    filial_2 = Filial("ES-MAD-01", "Filial Madrid", "Espana", "Madrid", "EUR", id_filial=2)
    producto = ProductoImportado.crear_con_conversion(
        codigo="LAP-001",
        nombre="Laptop de prueba",
        descripcion_tecnica="Equipo incluido en el reporte",
        categoria="Laptop",
        costo_unitario_cny="100.00",
        tasa_cny_eur="0.13000000",
        proveedor="Proveedor de prueba",
        fecha_importacion=date.today(),
    )
    producto.id_producto = 1

    def crear_venta(numero, id_filial):
        return TransaccionVenta(
            numero_factura=numero,
            id_filial=id_filial,
            fecha_venta=datetime.now().replace(microsecond=0),
            cliente="Cliente de prueba",
            vendedor="Vendedor de prueba",
            metodo_pago="Efectivo",
            codigo_divisa="PEN" if id_filial == 1 else "EUR",
            tasa_eur_aplicada="0.25000000" if id_filial == 1 else "1.00000000",
            detalles=[DetalleVenta(1, 2, "120.00", "13.00")],
        )

    ventas_guardadas = [crear_venta("F001-000001", 1), crear_venta("F002-000001", 2)]

    class RepositorioVentas:
        def listar_por_periodo(self, _inicio, _fin, id_filial=None):
            return [
                venta
                for venta in ventas_guardadas
                if id_filial is None or venta.id_filial == id_filial
            ]

    servicio = ServicioReportes(
        RepositorioVentas(),
        SimpleNamespace(listar=lambda: [filial_1, filial_2]),
        SimpleNamespace(listar=lambda: [producto]),
        FachadaSERF(),
    )
    reporte = servicio.generar(
        {
            "tipo": "mensual",
            "anio": date.today().year,
            "mes": date.today().month,
            "id_filial": 1,
            "con_marca_agua": False,
            "con_firma": False,
        }
    )

    assert reporte["cantidad_ventas"] == 1
    assert reporte["ventas"][0]["numero_factura"] == "F001-000001"
    assert reporte["periodo"]
    assert reporte["total_ingresos_eur"] == Decimal("60.00")
