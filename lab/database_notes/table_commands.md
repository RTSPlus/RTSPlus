CREATE TYPE capacity AS ENUM ('EMPTY', 'HALF_EMPTY', 'FULL');

CREATE TABLE BusLocation (
	entry_id integer,
	status capacity,
	vid integer,
	pid integer,
	rt integer,
	pdist int,
	coordinates point,
	req_time timestamp,
	destination varchar(255),
	PRIMARY KEY (entry_id)	
);

CREATE TABLE Stops(
	pid int,
	stop_coords point,
	PRIMARY KEY (pid)
);

CREATE TABLE Patterns(
	pid int,
	rtdir varchar(16),
	len integer,
	PRIMARY KEY(pid)
);
