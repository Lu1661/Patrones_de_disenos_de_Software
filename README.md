# SERF - Sistema Empresarial de Reportes Financieros

Proyecto académico del curso Patrones de Diseño de Software.

## Tecnologías

- Python 3.10 o superior
- Flask
- MySQL
- HTML, CSS y JavaScript
- pytest

## Estado actual

Las fases 1 a 12 están terminadas. El proyecto cuenta con estructura modular, base de datos MySQL, entidades del dominio, los seis patrones solicitados, repositorios, backend Flask, una interfaz web responsive, reportes financieros integrados y una suite automatizada de pruebas.

## Preparación local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

El archivo `.env` debe completarse localmente y nunca debe enviarse al repositorio.

## Ejecución

```powershell
python ejecutar.py
```

La aplicación quedará disponible en `http://127.0.0.1:5000`.

## Pruebas automatizadas

```powershell
python -m pytest -q
```

La suite contiene pruebas unitarias para las entidades, cálculos y seis patrones, además de pruebas de integración para Flask y MySQL. La prueba MySQL utiliza las variables del archivo `.env`, crea datos temporales y los elimina al finalizar. Si MySQL no está configurado, esa prueba se omite sin impedir la ejecución de las pruebas unitarias.

## API disponible

- `GET` y `POST` `/api/configuracion/filiales`
- `GET` y `POST` `/api/configuracion/tipos-cambio`
- `GET` y `POST` `/api/productos`
- `GET` `/api/inventario?id_filial=1`
- `POST` `/api/inventario/reponer`
- `GET` y `POST` `/api/ventas`
- `POST` `/api/reportes/generar`

Las respuestas utilizan JSON y mantienen la estructura `exito`, `mensaje` y `datos`. Los registros de producto y venta se ejecutan dentro de transacciones para evitar productos incompletos, ventas sin detalle o descuentos parciales de stock.

## Módulos de la interfaz

- Resumen general con indicadores operativos.
- Configuración de filiales y tipos de cambio.
- Registro y consulta de productos importados.
- Consulta y reposición de inventario por filial.
- Registro y consulta de ventas con conversión a EUR.
- Reportes mensuales, trimestrales y anuales por filial o consolidados.

La interfaz utiliza las rutas del backend mediante JavaScript y adapta formularios, navegación y tablas para equipos de escritorio y dispositivos móviles.

## Flujo integrado

El uso normal del sistema sigue este orden: registrar los tipos de cambio, crear una filial, registrar un producto con su stock inicial y finalmente realizar ventas. Cada venta consulta la tasa correspondiente, calcula los importes y descuenta el inventario dentro de una misma transacción. Si alguna operación falla, MySQL revierte el proceso para conservar datos consistentes.

Los reportes consultan las ventas históricas sin modificar datos. Presentan ingresos, gastos de importación y resultado financiero en EUR, una comparación sencilla entre filiales y una vista preparada para impresión. La marca de agua y la firma con SHA-256 son opciones académicas del reporte.

## Organización

- `aplicacion/dominio`: entidades y contratos del negocio.
- `aplicacion/servicios`: procesos principales del sistema.
- `aplicacion/reportes`: construcción y presentación de reportes.
- `aplicacion/persistencia`: conexión y repositorios MySQL.
- `aplicacion/presentacion`: controladores, plantillas y recursos visuales.
- `base_datos`: scripts SQL ordenados.
- `pruebas`: pruebas unitarias y de integración.

Los patrones solicitados se ubicarán dentro de los módulos donde cumplen una responsabilidad real. No se crearán carpetas separadas por patrón.

