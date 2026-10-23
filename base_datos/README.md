# Base de datos de SERF

La base de datos utiliza MySQL 8 y el motor InnoDB para conservar las relaciones y permitir transacciones en el registro de ventas.

## Orden de ejecución

1. `01_crear_tablas.sql`
2. `02_insertar_datos_iniciales.sql`
3. `03_consultas_verificacion.sql`

## Tablas

- `divisas`: monedas reconocidas por el sistema.
- `filiales`: sedes comerciales y su moneda local.
- `tipos_cambio`: tasas históricas de conversión hacia EUR.
- `productos_importados`: catálogo corporativo de productos.
- `inventarios_filial`: stock y precio local por filial.
- `ventas`: cabecera y totales de cada venta.
- `detalles_venta`: productos y cantidades de cada venta.

## Consideraciones

- Los importes monetarios utilizan `DECIMAL(14,2)`.
- Las tasas de cambio utilizan `DECIMAL(18,8)`.
- Los datos iniciales no incluyen tasas comerciales variables.
- Solamente se registra la equivalencia fija EUR/EUR con valor 1.
- La contraseña MySQL no se escribe en ningún script.
- La venta y la deducción de stock se controlarán dentro de una transacción desde el backend.

