# SERF - Definicion funcional para programacion

## 1. Proposito

Este documento fija los nombres, campos, reglas y alcance que se utilizaran para construir la base de datos, el backend y el frontend de SERF. Su contenido parte del entregable parcial y resuelve las diferencias de nombres que no deben trasladarse al codigo.

## 2. Alcance confirmado

El sistema permitira:

1. Registrar productos tecnologicos importados desde China.
2. Asignar el stock inicial y el precio local a una filial.
3. Consultar el inventario disponible por filial.
4. Registrar ventas en la moneda local de cada filial.
5. Descontar el stock automaticamente al confirmar una venta.
6. Convertir costos e importes a la moneda corporativa EUR.
7. Administrar filiales y tipos de cambio.
8. Generar reportes mensuales, trimestrales y anuales.
9. Generar reportes por filial o como consolidado corporativo.
10. Aplicar opcionalmente marca de agua y firma digital academica.

## 3. Modulos funcionales

- Inicio: resumen basico del sistema.
- Productos: registro y consulta de productos importados.
- Inventario: consulta de existencias y precios por filial.
- Ventas: registro y consulta de transacciones.
- Configuracion: mantenimiento de filiales y tipos de cambio.
- Reportes: generacion, visualizacion e impresion de reportes financieros.

## 4. Nombres oficiales del dominio

| Concepto | Nombre oficial en Python | Nombre sugerido en MySQL |
| --- | --- | --- |
| Filial comercial | `Filial` | `filiales` |
| Moneda | `Divisa` | `divisas` |
| Tipo de cambio hacia EUR | `TipoCambio` | `tipos_cambio` |
| Producto importado | `ProductoImportado` | `productos_importados` |
| Inventario por filial | `InventarioFilial` | `inventarios_filial` |
| Venta | `TransaccionVenta` | `ventas` |
| Producto incluido en una venta | `DetalleVenta` | `detalles_venta` |
| Servicio de existencias | `GestorStockFilial` | No corresponde |
| Configuracion compartida | `ConfiguracionGlobal` | No corresponde como entidad independiente |
| Acceso unificado | `FachadaSERF` | No corresponde |

## 5. Campos oficiales

### 5.1 Filial

- `id_filial`
- `codigo`
- `nombre`
- `pais`
- `ciudad`
- `codigo_divisa`
- `activa`

Reglas:

- El codigo de filial es unico.
- Cada filial utiliza una divisa local.
- Una filial inactiva no puede registrar nuevas ventas.

### 5.2 Divisa

- `codigo_iso`
- `nombre`
- `simbolo`
- `activa`

Reglas:

- El codigo ISO contiene tres letras mayusculas.
- EUR es la divisa corporativa.
- CNY es la divisa de los costos de importacion.

### 5.3 Tipo de cambio

- `id_tipo_cambio`
- `codigo_divisa_origen`
- `codigo_divisa_destino`
- `tasa`
- `fecha_vigencia`
- `activa`

Reglas:

- La divisa de destino sera EUR.
- La tasa representa cuantos EUR equivalen a una unidad de la divisa de origen.
- La conversion se calcula con `monto_origen * tasa`.
- La tasa debe ser mayor que cero.
- Solo puede existir una tasa activa por divisa de origen.
- Si la divisa de origen es EUR, la tasa utilizada sera 1.

### 5.4 Producto importado

- `id_producto`
- `codigo`
- `nombre`
- `descripcion_tecnica`
- `categoria`
- `costo_unitario_cny`
- `costo_unitario_eur`
- `proveedor`
- `fecha_importacion`
- `activo`

Categorias permitidas:

- Laptop
- Smartphone
- Accesorio
- Redes

Reglas:

- El codigo es unico.
- El nombre, la categoria y el proveedor son obligatorios.
- El costo en CNY debe ser mayor que cero.
- El costo en EUR se calcula con la tasa CNY/EUR vigente.
- La fecha de importacion no puede ser futura.

### 5.5 Inventario por filial

- `id_inventario`
- `id_filial`
- `id_producto`
- `stock_disponible`
- `precio_venta_local`
- `fecha_actualizacion`

Reglas:

- La combinacion filial-producto es unica.
- El stock nunca puede ser negativo.
- El precio de venta local debe ser mayor que cero.
- El precio se guarda en la divisa local de la filial.
- El stock inicial se registra en la filial de destino indicada al crear el producto.

### 5.6 Transaccion de venta

- `id_venta`
- `numero_factura`
- `id_filial`
- `fecha_venta`
- `cliente`
- `vendedor`
- `metodo_pago`
- `codigo_divisa`
- `tasa_eur_aplicada`
- `total_local`
- `total_eur`

Metodos de pago permitidos:

- Efectivo
- Tarjeta
- Transferencia

Reglas:

- El numero de factura es unico.
- La fecha de venta no puede ser futura.
- La divisa de la venta corresponde a la filial.
- La tasa y los importes utilizados quedan guardados para conservar el valor historico.
- La venta, sus detalles y el descuento de stock forman una sola transaccion de base de datos.

### 5.7 Detalle de venta

- `id_detalle`
- `id_venta`
- `id_producto`
- `cantidad`
- `precio_unitario_local`
- `subtotal_local`
- `costo_unitario_eur`
- `subtotal_costo_eur`

Reglas:

- La cantidad debe ser mayor que cero.
- El precio unitario debe ser mayor que cero.
- El subtotal local se calcula con `cantidad * precio_unitario_local`.
- El costo se conserva para que los reportes historicos no cambien si luego cambia el costo del producto.
- La primera interfaz podra registrar un producto por venta, pero la estructura permitira varios detalles.

## 6. Reglas generales del negocio

1. Los importes monetarios se manejaran con `Decimal`, nunca con `float`.
2. Los importes visibles se redondearan a dos decimales.
3. Las tasas de cambio conservaran hasta ocho decimales.
4. No se guardara un producto si falta la tasa CNY/EUR.
5. No se guardara una venta si falta la tasa de la divisa local hacia EUR.
6. No se permitira vender una cantidad mayor al stock disponible.
7. Si falla cualquier parte de una venta, no se guardara la venta y no se modificara el inventario.
8. Las consultas y reportes no modificaran productos, ventas ni inventarios.
9. Un periodo sin ventas generara un reporte valido con importes en cero.
10. Los gastos de importacion del reporte se calcularan con la suma del costo unitario historico en EUR multiplicado por las unidades vendidas.
11. El resultado financiero basico sera `ingresos_eur - gastos_importacion_eur`.

## 7. Formularios confirmados

### 7.1 Registrar producto importado

- Codigo
- Nombre comercial
- Descripcion tecnica
- Categoria
- Costo unitario CNY
- Proveedor
- Fecha de importacion
- Filial de destino
- Stock inicial
- Precio de venta local

### 7.2 Registrar venta

- Numero de factura
- Fecha de venta
- Filial
- Cliente
- Vendedor
- Metodo de pago
- Producto
- Cantidad
- Precio unitario local, precargado desde el inventario y editable

### 7.3 Administrar tipo de cambio

- Divisa de origen
- Tasa hacia EUR
- Fecha de vigencia

### 7.4 Generar reporte

- Tipo: mensual, trimestral o anual
- Periodo correspondiente
- Filial especifica o consolidado corporativo
- Aplicar marca de agua
- Aplicar firma digital academica

## 8. Contenido minimo de los reportes

- Encabezado corporativo.
- Tipo y periodo del reporte.
- Fecha de generacion.
- Filial seleccionada o consolidado corporativo.
- Ingresos en EUR.
- Gastos de importacion en EUR.
- Resultado financiero en EUR.
- Secciones por pais, filial y categoria.
- Tabla de ventas.
- Grafico comparativo sencillo entre filiales.
- Conclusion generada mediante reglas simples.
- Indicacion de periodo sin movimientos cuando corresponda.

La salida inicial sera una vista HTML preparada para impresion. El navegador permitira guardarla como PDF sin agregar una biblioteca compleja al proyecto.

## 9. Aplicacion limitada de patrones

| Patron | Clases oficiales | Aplicacion exclusiva |
| --- | --- | --- |
| Singleton | `ConfiguracionGlobal` | Tasas, moneda corporativa y redondeo compartidos durante la ejecucion |
| Prototype | `IReportePrototype`, `ReporteMensual`, `ReporteTrimestral`, `ReporteAnual` | Clonacion profunda de las plantillas base |
| Builder | `IReporteBuilder`, `ReporteFinancieroBuilder`, `DirectorReporte` | Construccion ordenada del reporte |
| Composite | `ComponenteReporte`, `SeccionCompuesta`, `RegistroVentaHoja` | Arbol de secciones y registros del reporte |
| Decorator | `IReporteFinanciero`, `ReporteBase`, `ReporteDecorator`, `MarcaDeAguaDecorator`, `FirmaDigitalDecorator` | Sellos opcionales del reporte terminado |
| Facade | `FachadaSERF` | Punto de entrada simplificado para generar el reporte consolidado |

No se agregaran otros patrones si no existe una necesidad funcional demostrable.

## 10. Firma digital academica

Para el alcance del parcial, la firma digital consistira en:

- Hash SHA-256 del contenido final.
- Fecha y hora de generacion.
- Nombre del emisor corporativo configurado.
- Identificador de firma.

Esta funcion demuestra el Decorator y la integridad del contenido, pero no se presentara como una firma digital con validez legal ni requerira la compra de un certificado real.

## 11. Alcance de acceso de usuarios

Los actores de la documentacion se conservaran para describir quien utiliza cada proceso. No se construira un modulo de inicio de sesion, usuarios o permisos porque no existe un requisito funcional especifico para ese modulo en el parcial.

Las pantallas se organizaran de acuerdo con las tareas de los actores, sin impedir el acceso mediante autenticacion.

## 12. Convenciones del codigo

- Carpetas, archivos, variables y funciones en español sin tildes ni letra eñe.
- Clases en `PascalCase`.
- Variables, funciones y archivos en `snake_case`.
- Comentarios por clase, funcion o bloque de negocio importante.
- Comentarios relacionados con los requisitos `RF` y casos de uso `CU` cuando corresponda.
- Sin carpetas organizadas por nombre de patron.
- Sin abstracciones adicionales que no aporten al caso practico.

## 13. Repositorio del proyecto

- Repositorio personal previsto: `https://github.com/Lu1661/Patrones_de_disenos_de_Software`.
- Este proyecto no pertenece a Zentro y no debe compartir remotos, cuentas, codigo ni configuraciones con repositorios de Zentro.
- Git se inicializara desde el comienzo de la estructura para conservar el historial solicitado por la rubrica.
- La vinculacion y publicacion en GitHub se realizara en una fase autorizada y despues de verificar la cuenta personal activa.
- Las credenciales MySQL, archivos `.env` y datos sensibles nunca se versionaran.

## 14. Puntos de documentacion que se revisaran al final

1. Stack definitivo Python, Flask, MySQL, HTML, CSS, JavaScript y pytest.
2. Correccion del titulo ISP que contiene la explicacion de DIP.
3. Unificacion de nombres de clases con este documento.
4. Diagrama de clases basado en la implementacion real.
5. Diagramas de secuencia y colaboracion basados en los flujos terminados.
6. Estados reales de TC-01 a TC-06 y sus evidencias.
7. Capturas de ejecucion y base de datos.
8. Capturas de Figma elaboradas a partir del sistema terminado.
9. Evidencias reales de usabilidad.
10. Estructura definitiva del proyecto.
11. Diccionario de datos de MySQL.
12. Instrucciones de instalacion y ejecucion.
13. Distribucion del trabajo.
14. Aclaracion de que la firma implementada es una demostracion academica con SHA-256.

## 15. Criterio de cierre de esta fase

Los nombres, campos, reglas, formularios y alcance establecidos en este archivo se consideran la referencia para las siguientes fases. Cualquier cambio posterior debera responder a una necesidad descubierta durante la implementacion y quedara registrado para la revision final de la documentacion.
