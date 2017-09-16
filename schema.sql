create table entries (
	id integer primary key autoincrement,
	winery text not null,
	location text,
	vintage int not null,
	style text not null,
	vineyard text,
	rating int,
	thoughts text,
	flavours text,
	drank int not null,
	username string,
	photo blob,
	FOREIGN KEY(username) REFERENCES users(username)
);

create table users (
	id integer primary key autoincrement,
	username string not null,
	password string not null
);
