-- ============================================================
-- PROYECTO: SERF
-- ARCHIVO: CREACION DE LA ESTRUCTURA PRINCIPAL
-- BASE DE DATOS: financorp_db
-- ============================================================

USE financorp_db;

SET NAMES utf8mb4;

-- ============================================================
-- BLOQUE: CATALOGO DE DIVISAS
-- Este bloque almacena las monedas utilizadas por las filiales,
-- las importaciones y la consolidacion corporativa en EUR.
-- Cumple: RF-04 y CU-04.
-- ============================================================
CREATE TABLE IF NOT EXISTS divisas (
    codigo_iso CHAR(3) NOT NULL,
    nombre VARCHAR(60) NOT NULL,
    simbolo VARCHAR(10) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (codigo_iso),
    CONSTRAINT chk_divisas_codigo
        CHECK (codigo_iso REGEXP '^[A-Z]{3}$')
) ENGINE = InnoDB;

-- ============================================================
-- BLOQUE: REGISTRO DE FILIALES
-- Este bloque identifica cada sede comercial y la divisa local
-- que debe utilizarse en sus operaciones de venta.
-- Cumple: CU-05.
-- ============================================================
CREATE TABLE IF NOT EXISTS filiales (
    id_filial BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo VARCHAR(15) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(80) NOT NULL,
    ciudad VARCHAR(80) NOT NULL,
    codigo_divisa CHAR(3) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_filial),
    UNIQUE KEY uq_filiales_codigo (codigo),
    KEY idx_filiales_divisa (codigo_divisa),
    CONSTRAINT fk_filiales_divisa
        FOREIGN KEY (codigo_divisa)
        REFERENCES divisas (codigo_iso)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB;

-- ============================================================
-- BLOQUE: TIPOS DE CAMBIO HACIA EUR
-- Este bloque conserva las tasas historicas usadas para convertir
-- costos e importes sin modificar operaciones ya registradas.
-- Cumple: RF-04, CU-04 y CU-05.
-- ============================================================
CREATE TABLE IF NOT EXISTS tipos_cambio (
    id_tipo_cambio BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo_divisa_origen CHAR(3) NOT NULL,
    codigo_divisa_destino CHAR(3) NOT NULL DEFAULT 'EUR',
    tasa DECIMAL(18,8) NOT NULL,
    fecha_vigencia DATE NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_tipo_cambio),
    UNIQUE KEY uq_tipos_cambio_fecha (
        codigo_divisa_origen,
        codigo_divisa_destino,
        fecha_vigencia
    ),
    KEY idx_tipos_cambio_busqueda (
        codigo_divisa_origen,
        codigo_divisa_destino,
        activa,
        fecha_vigencia
    ),
    CONSTRAINT fk_tipos_cambio_origen
        FOREIGN KEY (codigo_divisa_origen)
        REFERENCES divisas (codigo_iso)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_tipos_cambio_destino
        FOREIGN KEY (codigo_divisa_destino)
        REFERENCES divisas (codigo_iso)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT chk_tipos_cambio_tasa
        CHECK (tasa > 0),
    CONSTRAINT chk_tipos_cambio_destino_eur
        CHECK (codigo_divisa_destino = 'EUR')
) ENGINE = InnoDB;

-- ============================================================
-- BLOQUE: CATALOGO DE PRODUCTOS IMPORTADOS
-- Este bloque registra los datos tecnicos y costos de los productos
-- adquiridos en CNY y convertidos a EUR al momento del ingreso.
-- Cumple: RF-01 y CU-01.
-- ============================================================
CREATE TABLE IF NOT EXISTS productos_importados (
    id_producto BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    descripcion_tecnica TEXT NOT NULL,
    categoria VARCHAR(20) NOT NULL,
    costo_unitario_cny DECIMAL(14,2) NOT NULL,
    costo_unitario_eur DECIMAL(14,2) NOT NULL,
    proveedor VARCHAR(120) NOT NULL,
    fecha_importacion DATE NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_producto),
    UNIQUE KEY uq_productos_codigo (codigo),
    KEY idx_productos_nombre (nombre),
    KEY idx_productos_categoria (categoria),
    CONSTRAINT chk_productos_categoria
        CHECK (categoria IN ('Laptop', 'Smartphone', 'Accesorio', 'Redes')),
    CONSTRAINT chk_productos_costo_cny
        CHECK (costo_unitario_cny > 0),
    CONSTRAINT chk_productos_costo_eur
        CHECK (costo_unitario_eur > 0)
) ENGINE = InnoDB;

-- ============================================================
-- BLOQUE: INVENTARIO LOCAL POR FILIAL
-- Este bloque separa el producto corporativo de sus existencias y
-- del precio de venta configurado en la moneda local de cada filial.
-- Cumple: RF-01, RF-03, CU-01 y CU-03.
-- ============================================================
CREATE TABLE IF NOT EXISTS inventarios_filial (
    id_inventario BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_filial BIGINT UNSIGNED NOT NULL,
    id_producto BIGINT UNSIGNED NOT NULL,
    stock_disponible INT UNSIGNED NOT NULL DEFAULT 0,
    precio_venta_local DECIMAL(14,2) NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_inventario),
    UNIQUE KEY uq_inventario_filial_producto (id_filial, id_producto),
    KEY idx_inventario_producto (id_producto),
    KEY idx_inventario_stock (id_filial, stock_disponible),
    CONSTRAINT fk_inventario_filial
        FOREIGN KEY (id_filial)
        REFERENCES filiales (id_filial)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_inventario_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos_importados (id_producto)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_inventario_stock
        CHECK (stock_disponible >= 0),
    CONSTRAINT chk_inventario_precio
        CHECK (precio_venta_local > 0)
) ENGINE = InnoDB;

-- ============================================================
-- BLOQUE: CABECERA DE TRANSACCIONES DE VENTA
-- Este bloque conserva la filial, moneda, tasa e importes finales
-- empleados en cada comprobante para mantener su valor historico.
-- Cumple: RF-02, RF-03, RF-04 y CU-02.
-- ============================================================
CREATE TABLE IF NOT EXISTS ventas (
    id_venta BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    numero_factura VARCHAR(40) NOT NULL,
    id_filial BIGINT UNSIGNED NOT NULL,
    fecha_venta DATETIME NOT NULL,
    cliente VARCHAR(120) NOT NULL,
    vendedor VARCHAR(120) NOT NULL,
    metodo_pago VARCHAR(20) NOT NULL,
    codigo_divisa CHAR(3) NOT NULL,
    tasa_eur_aplicada DECIMAL(18,8) NOT NULL,
    total_local DECIMAL(14,2) NOT NULL,
    total_eur DECIMAL(14,2) NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_venta),
    UNIQUE KEY uq_ventas_numero_factura (numero_factura),
    KEY idx_ventas_filial_fecha (id_filial, fecha_venta),
    KEY idx_ventas_divisa (codigo_divisa),
    CONSTRAINT fk_ventas_filial
        FOREIGN KEY (id_filial)
        REFERENCES filiales (id_filial)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_ventas_divisa
        FOREIGN KEY (codigo_divisa)
        REFERENCES divisas (codigo_iso)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_ventas_metodo_pago
        CHECK (metodo_pago IN ('Efectivo', 'Tarjeta', 'Transferencia')),
    CONSTRAINT chk_ventas_tasa
        CHECK (tasa_eur_aplicada > 0),
    CONSTRAINT chk_ventas_total_local
        CHECK (total_local > 0),
    CONSTRAINT chk_ventas_total_eur
        CHECK (total_eur > 0)
) ENGINE = InnoDB;

-- ============================================================
-- BLOQUE: DETALLES DE CADA VENTA
-- Este bloque registra productos, cantidades, precios y costos
-- historicos para construir reportes financieros consistentes.
-- Cumple: RF-02, RF-06, RF-07 y CU-02.
-- ============================================================
CREATE TABLE IF NOT EXISTS detalles_venta (
    id_detalle BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_venta BIGINT UNSIGNED NOT NULL,
    id_producto BIGINT UNSIGNED NOT NULL,
    cantidad INT UNSIGNED NOT NULL,
    precio_unitario_local DECIMAL(14,2) NOT NULL,
    subtotal_local DECIMAL(14,2) NOT NULL,
    costo_unitario_eur DECIMAL(14,2) NOT NULL,
    subtotal_costo_eur DECIMAL(14,2) NOT NULL,
    PRIMARY KEY (id_detalle),
    UNIQUE KEY uq_detalle_venta_producto (id_venta, id_producto),
    KEY idx_detalles_producto (id_producto),
    CONSTRAINT fk_detalles_venta
        FOREIGN KEY (id_venta)
        REFERENCES ventas (id_venta)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_detalles_producto
        FOREIGN KEY (id_producto)
        REFERENCES productos_importados (id_producto)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_detalles_cantidad
        CHECK (cantidad > 0),
    CONSTRAINT chk_detalles_precio
        CHECK (precio_unitario_local > 0),
    CONSTRAINT chk_detalles_subtotal
        CHECK (subtotal_local > 0),
    CONSTRAINT chk_detalles_costo
        CHECK (costo_unitario_eur > 0),
    CONSTRAINT chk_detalles_subtotal_costo
        CHECK (subtotal_costo_eur > 0)
) ENGINE = InnoDB;

