# SERF - Sistema Empresarial de Reportes Financieros

Proyecto académico del curso Patrones de Diseño de Software.

## Tecnologías

- Python 3.10 o superior
- Flask
- MySQL
- HTML, CSS y JavaScript
- pytest

## Estado actual

Las fases 1 a 8 están terminadas. El proyecto cuenta con estructura modular, base de datos MySQL, entidades del dominio, los seis patrones solicitados, repositorios y un backend Flask funcional. La interfaz web se implementará en la fase siguiente.

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

## API disponible

- `GET` y `POST` `/api/configuracion/filiales`
- `GET` y `POST` `/api/configuracion/tipos-cambio`
- `GET` y `POST` `/api/productos`
- `GET` `/api/inventario?id_filial=1`
- `POST` `/api/inventario/reponer`
- `GET` y `POST` `/api/ventas`

Las respuestas utilizan JSON y mantienen la estructura `exito`, `mensaje` y `datos`. Los registros de producto y venta se ejecutan dentro de transacciones para evitar productos incompletos, ventas sin detalle o descuentos parciales de stock.

## Organización

- `aplicacion/dominio`: entidades y contratos del negocio.
- `aplicacion/servicios`: procesos principales del sistema.
- `aplicacion/reportes`: construcción y presentación de reportes.
- `aplicacion/persistencia`: conexión y repositorios MySQL.
- `aplicacion/presentacion`: controladores, plantillas y recursos visuales.
- `base_datos`: scripts SQL ordenados.
- `pruebas`: pruebas unitarias y de integración.

Los patrones solicitados se ubicarán dentro de los módulos donde cumplen una responsabilidad real. No se crearán carpetas separadas por patrón.

