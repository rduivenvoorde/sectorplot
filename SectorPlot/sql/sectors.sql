-- Table: sectors

-- DROP TABLE sectors;

CREATE TABLE sectors
(
  id serial NOT NULL,
  name varchar(50),
  x float,
  y float,
  mindistance float,
  maxdistance float,
  direction float,
  angle float,
  countermeasure varchar(10),
  z_order integer,
  savetime timestamp,
  countermeasuretime timestamp,
  geom geometry(Polygon, 4326),
  CONSTRAINT sectors_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE sectors
  OWNER TO postgres;

select * from sectors;

INSERT INTO sectors (name, x, y, mindistance, maxdistance, direction, angle, countermeasure, z_order, savetime, countermeasuretime, geom)
            VALUES ('test', 10, 20, 0, 5000, 45, 45, 'jodium', 0, '2003-1-1 20:30:00'::timestamp, '2003-1-1 20:30:00'::timestamp, ST_GeomFromText('Polygon((0 0,1 1,1 0,0 0))',4326));


