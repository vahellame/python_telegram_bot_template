create table users(
	telegram_id integer PRIMARY KEY,
	username varchar,
	datetime_added timestamptz,
	datetime_last_usage timestamptz,
	current_state_info jsonb);

create table texts(
	id serial PRIMARY KEY,
	title varchar,
	text varchar);

create table photos(
	id serial PRIMARY KEY,
	title varchar,
	raw bytea);

create table videos(
	id serial PRIMARY KEY,
	title varchar,
	raw bytea);

create table video_notes(
	id serial PRIMARY KEY,
	title varchar,
	raw bytea);
