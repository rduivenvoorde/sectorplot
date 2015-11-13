-- Table: sectors

-- DROP TABLE sectors;

CREATE TABLE sectors
(
  id serial NOT NULL,
  geom geometry(Polygon, 4326),
  x float,
  y float,
  distance float,
  direction float,
  angle float,
  type varchar(10),
  z_order integer,
  savetime timestamp,
  CONSTRAINT sectors_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE sectors
  OWNER TO postgres;

select * from sectors;

INSERT INTO sectors (x, y, distance, direction, angle, type, z_order, geom, savetime) VALUES (10, 20, 5000, 45, 45, 'jodium', 0, ST_GeomFromText('Polygon((0 0,1 1,1 0,0 0))',4326), '2003-1-1 20:30:00'::timestamp);


