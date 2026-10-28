# SERF - Sistema Empresarial de Reportes Financieros

SERF es un proyecto académico desarrollado para el curso de Patrones de Diseño de Software. El sistema permite registrar productos importados, controlar el inventario de varias filiales, guardar ventas y generar reportes financieros en euros.

## Objetivo del proyecto

El objetivo es reunir la información comercial de FinanCorp en una aplicación sencilla. Cada filial trabaja con su moneda local y el sistema utiliza los tipos de cambio registrados para mostrar resultados consolidados en EUR.

## Funciones principales

- Registrar tipos de cambio y filiales.
- Registrar productos importados y su stock inicial.
- Consultar y reponer el inventario de cada filial.
- Registrar ventas y descontar el stock utilizado.
- Consultar ventas por fechas y por filial.
- Generar reportes mensuales, trimestrales y anuales.
- Agregar una marca de agua o una firma digital al reporte.
- Editar o desactivar registros desde la cuenta administrativa.

## Patrones utilizados

El proyecto utiliza los seis patrones solicitados en el caso práctico:

- **Singleton:** mantiene una sola configuración de tipos de cambio durante la ejecución.
- **Prototype:** crea una copia de la plantilla del reporte elegido.
- **Builder:** arma el reporte paso a paso.
- **Composite:** organiza el contenido del reporte por grupos y elementos.
- **Decorator:** agrega la marca de agua y la firma digital de manera opcional.
- **Facade:** ofrece un punto sencillo para coordinar la generación del reporte.

Los patrones están dentro de los módulos donde cumplen una función real. No se crearon carpetas separadas para cada patrón.

## Tecnologías

- Python 3.10 o superior
- Flask
- MySQL
- HTML, CSS y JavaScript
- pytest

## Organización del proyecto

- `aplicacion/configuracion`: configuración de Flask y del sistema.
- `aplicacion/dominio`: entidades, validaciones y contratos principales.
- `aplicacion/servicios`: procesos de filiales, productos, inventario y ventas.
- `aplicacion/reportes`: clases utilizadas para generar los reportes.
- `aplicacion/persistencia`: conexión y consultas a MySQL.
- `aplicacion/presentacion`: rutas, pantallas y recursos de la interfaz.
- `base_datos`: scripts para crear y preparar la base de datos.
- `pruebas`: pruebas unitarias y de integración.

## Preparación local

Desde la carpeta principal del proyecto se ejecutan los siguientes comandos:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Luego se completan en `.env` los datos de conexión a MySQL. Este archivo es local y no debe enviarse al repositorio.

## Ejecución

Con el entorno virtual activo se inicia el sistema con:

```powershell
python ejecutar.py
```

La aplicación estará disponible en `http://127.0.0.1:5000`.

El usuario y la contraseña local se encuentran en `ARRANQUE.txt`. También pueden cambiarse con las variables `ADMIN_USUARIO` y `ADMIN_PASSWORD` del archivo `.env`.

## Orden básico de uso

1. Registrar los tipos de cambio.
2. Crear una filial y seleccionar su moneda local.
3. Registrar un producto con su stock y precio de venta.
4. Revisar el inventario disponible.
5. Registrar una venta.
6. Generar el reporte del periodo elegido.

## Pruebas

Las pruebas se ejecutan desde la carpeta principal:

```powershell
python -m pytest -q
```

Las pruebas unitarias revisan las reglas principales y los patrones de diseño. La prueba de integración con MySQL se ejecuta cuando la conexión está configurada en el entorno local.
