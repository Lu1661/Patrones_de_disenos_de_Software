-- ============================================================
-- PROYECTO: SERF
-- MIGRACION: CATEGORIAS Y NUMERACION DE FACTURAS POR FILIAL
-- Ejecutar una sola vez sobre una base creada con la version anterior.
-- ============================================================

SET NAMES utf8mb4;

CREATE TABLE categorias_productos (
    id_categoria BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_categoria),
    UNIQUE KEY uq_categorias_productos_nombre (nombre)
) ENGINE = InnoDB;

INSERT INTO categorias_productos (nombre, activa)
VALUES
    ('Laptop', TRUE),
    ('Smartphone', TRUE),
    ('Accesorio', TRUE),
    ('Redes', TRUE);

ALTER TABLE productos_importados
    DROP CHECK chk_productos_categoria,
    MODIFY categoria VARCHAR(50) NOT NULL,
    ADD CONSTRAINT fk_productos_categoria
        FOREIGN KEY (categoria)
        REFERENCES categorias_productos (nombre)
        ON UPDATE CASCADE
        ON DELETE RESTRICT;

ALTER TABLE filiales
    ADD serie_factura CHAR(4) NULL AFTER codigo_divisa,
    ADD ultimo_correlativo_factura INT UNSIGNED NOT NULL DEFAULT 0
        AFTER serie_factura;

UPDATE filiales SET serie_factura = 'F001' WHERE codigo = 'PE-LIM-01';
UPDATE filiales SET serie_factura = 'F002' WHERE codigo = 'ES-MAD-01';
UPDATE filiales SET serie_factura = 'F003' WHERE codigo = 'XI-SHE-01';
UPDATE filiales SET serie_factura = 'F004' WHERE codigo = 'XI-SHE-02';
UPDATE filiales SET serie_factura = 'F005' WHERE codigo = 'EU-NEWYORK_01';

SET @ultima_serie = (
    SELECT COALESCE(MAX(CAST(SUBSTRING(serie_factura, 2) AS UNSIGNED)), 0)
    FROM filiales
);

CREATE TEMPORARY TABLE series_pendientes AS
SELECT id_filial,
       CONCAT('F', LPAD(@ultima_serie + ROW_NUMBER() OVER (ORDER BY id_filial), 3, '0'))
           AS serie_factura
FROM filiales
WHERE serie_factura IS NULL;

UPDATE filiales AS filial
JOIN series_pendientes AS pendiente USING (id_filial)
SET filial.serie_factura = pendiente.serie_factura;

DROP TEMPORARY TABLE series_pendientes;

ALTER TABLE filiales
    MODIFY serie_factura CHAR(4) NOT NULL,
    ADD UNIQUE KEY uq_filiales_serie_factura (serie_factura),
    ADD CONSTRAINT chk_filiales_serie_factura
        CHECK (serie_factura REGEXP '^F[0-9]{3}$'),
    ADD CONSTRAINT chk_filiales_correlativo_factura
        CHECK (ultimo_correlativo_factura <= 999999);

UPDATE ventas
SET numero_factura = CONCAT('T', LPAD(id_venta, 10, '0'));

CREATE TEMPORARY TABLE facturas_ordenadas AS
SELECT venta.id_venta,
       venta.id_filial,
       ROW_NUMBER() OVER (
           PARTITION BY venta.id_filial
           ORDER BY venta.fecha_venta, venta.id_venta
       ) AS correlativo,
       CONCAT(
           filial.serie_factura,
           '-',
           LPAD(
               ROW_NUMBER() OVER (
                   PARTITION BY venta.id_filial
                   ORDER BY venta.fecha_venta, venta.id_venta
               ),
               6,
               '0'
           )
       ) AS numero_factura
FROM ventas AS venta
JOIN filiales AS filial USING (id_filial);

UPDATE ventas AS venta
JOIN facturas_ordenadas AS ordenada USING (id_venta)
SET venta.numero_factura = ordenada.numero_factura;

UPDATE filiales AS filial
LEFT JOIN (
    SELECT id_filial, MAX(correlativo) AS ultimo_correlativo
    FROM facturas_ordenadas
    GROUP BY id_filial
) AS resumen USING (id_filial)
SET filial.ultimo_correlativo_factura = COALESCE(resumen.ultimo_correlativo, 0);

DROP TEMPORARY TABLE facturas_ordenadas;

ALTER TABLE ventas
    MODIFY numero_factura CHAR(11) NOT NULL,
    ADD CONSTRAINT chk_ventas_numero_factura
        CHECK (numero_factura REGEXP '^F[0-9]{3}-[0-9]{6}$');
