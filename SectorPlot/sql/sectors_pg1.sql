﻿-- Table: sectors
-- Creation script to create sectors table in a Postgresql 8.4 database
-- DROP TABLE sectors;

CREATE TABLE sectors
(
  id serial NOT NULL,
  setname character varying(50),
  lon double precision,
  lat double precision,
  npp_block  character varying(50),
  mindistance double precision,
  maxdistance double precision,
  direction double precision,
  angle double precision,
  countermeasureid integer,
  z_order integer,
  savetime timestamp without time zone,
  countermeasuretime timestamp without time zone,
  sectorname character varying(50),
  setid integer,
  color character varying(9),
  CONSTRAINT sectors_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE sectors
  OWNER TO sectorplot;

SELECT AddGeometryColumn ('public','sectors','geom',4326,'POLYGON',2);

-- SELECT * FROM sectors;

-- DELETE FROM sectors;

-- NOTE!!!! the role sectorplot used by the geoserver should have priviliges enough to see the views + geom tables etc
-- else error: "Trying to create new feature type inside the store, but no attributes were specified"
-- see: http://osgeo-org.1560.x6.nabble.com/Problem-with-RESTful-creation-of-layers-based-on-Postgis-tables-td3790217.html
GRANT ALL ON SCHEMA public TO sectorplot;
GRANT ALL ON TABLE geography_columns TO sectorplot;
GRANT ALL ON TABLE geometry_columns TO sectorplot;