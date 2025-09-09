create table if not exists Person(
	id_p serial primary key,
	email text not null,
	phone bigint not null,
	city text not null,
	ready_to_move text,
	des_position text not null,
	experience text,
	education text,
	skills text not null
);

create table if not exists Vacancy(
	id_vac serial primary key,
	title text not null,
	city text not null,
	schedule text,
	type_of_employ text,
	duties text not null,
	requirements text not null,
	experience text,
	education text
);

create table if not exists 	Hr(
	id_hr serial primary key,
	id_vac int,
	FOREIGN KEY (id_vac) REFERENCES Vacancy(id_vac)
);

create table if not exists 	Report(
	id_rep serial primary key,
	id_p int,
	id_vac int,
	rep2hr text not null,
	rep2per text not null,
	FOREIGN KEY (id_p) REFERENCES Person(id_p),
	FOREIGN KEY (id_vac) REFERENCES Vacancy(id_vac)
);
