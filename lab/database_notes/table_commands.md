CREATE TYPE capacity AS ENUM ('EMPTY', 'HALF_EMPTY', 'FULL');

CREATE TABLE BusLocation (
	passengers capacity, 
	patternid integer,
	vehicleid integer,
	routeid integer, 
	pdist integer, 
	coordinates point, 
	request_time timestamp, 
	destination varchar, 
	PRIMARY KEY (request_time, vehicleid) 
);

CREATE TABLE Stops( 
	stopid integer,
	stopname varchar,
	patternid integer[], 
	stop_coordinates point, 
	PRIMARY KEY (stopid) 
);

CREATE TABLE ROUTE(
	routeid integer,
	routename varchar,
	PRIMARY KEY (routeid)
);

CREATE TABLE DETOUR(
	detourid integer,
	startdate timestamp,
	enddate timestamp,
	PRIMARY KEY (detourid)
);


CREATE TABLE Patterns(
	patternid integer,
	routeid integer,
	routedirection varchar(16),
	reportedlength integer, 
	calculatedlength integer,
	stops integer[][],
	waypoints integer[][],
	detourid integer,
	detourstops integer [][],
	detourwaypoints integer [][],
	PRIMARY KEY(patternid) 
);

