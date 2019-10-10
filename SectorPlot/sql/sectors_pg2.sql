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
ALTER TABLE sectors
  OWNER TO sectorplot_owner;

-- create extension postgis;
-- select version()



-- NOTE!!!! the role sectorplot used by the geoserver should have priviliges enough to see the views + geom tables etc
-- else error: "Trying to create new feature type inside the store, but no attributes were specified"
-- see: http://osgeo-org.1560.x6.nabble.com/Problem-with-RESTful-creation-of-layers-based-on-Postgis-tables-td3790217.html

-- sector specific
-- REVOKE ALL ON TABLE sectors from sectorplot;
GRANT SELECT, INSERT,UPDATE ON TABLE sectors TO sectorplot;
-- REVOKE ALL ON SEQUENCE sectors_id_seq FROM sectorplot;
GRANT USAGE, SELECT ON TABLE sectors_id_seq TO sectorplot;

-- postgis specific
-- REVOKE ALL ON spatial_ref_sys FROM sectorplot;
GRANT SELECT ON spatial_ref_sys TO sectorplot;
-- REVOKE ALL ON geography_columns FROM sectorplot;
GRANT SELECT ON geography_columns TO sectorplot;
-- REVOKE ALL ON geometry_columns FROM sectorplot;
GRANT SELECT ON geometry_columns TO sectorplot;

-- drop table pies
CREATE TABLE pies
(
  id serial NOT NULL,
  sectorset_id int,
  lon float,
  lat float,
  start_angle float,
  sector_count int,
  zone_radii varchar(50),
  geom geometry(MultiPolygon, 4326),
  CONSTRAINT pies_pkey PRIMARY KEY (id)
);
ALTER TABLE pies OWNER TO sectorplot_owner;
GRANT SELECT, UPDATE, INSERT ON TABLE pies TO sectorplot;

-- not sure if this is to be done....????
GRANT SELECT, USAGE ON SEQUENCE public.pies_id_seq TO sectorplot;
GRANT ALL ON SEQUENCE public.pies_id_seq TO sectorplot_owner;


-- TESTS AND INFO

select * from pies

select id, setname, lon, lat, setid from sectors order by setid desc
