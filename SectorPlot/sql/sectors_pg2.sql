-- Table: sectors
-- Creation script to create sectors table in a Postgresql 9.x database
-- DROP TABLE sectors;

CREATE TABLE sectors
(
  id serial NOT NULL,
  setname varchar(50),
  lon float,
  lat float,
  npp_block varchar(50),
  mindistance float,
  maxdistance float,
  direction float,
  angle float,
  countermeasureid integer,
  z_order integer,
  savetime timestamp,
  countermeasuretime timestamp,
  sectorname varchar(50),
  setid integer,
  color varchar(9),
  geom geometry(Polygon, 4326),
  CONSTRAINT sectors_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
-- ALTER TABLE sectors
--   OWNER TO postgres;

-- create extension postgis;
-- select version()



-- select * from sectors;

-- delete from sectors where left(name,1)='d';

-- werkt niet meer:
-- INSERT INTO sectors (x, y, distance, direction, angle, type, z_order, geom, savetime) VALUES (10, 20, 5000, 45, 45, 'jodium', 0, ST_GeomFromText('Polygon((0 0,1 1,1 0,0 0))',4326), '2003-1-1 20:30:00'::timestamp);

