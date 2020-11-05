#!/usr/bin/bash

PROJECT_FOLDER_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 || exit ; pwd -P )"
PROJECT_INTERPRETER_PATH="$PROJECT_FOLDER_PATH/venv/bin/python3"

echo "CREATING DATABASE"
read -rp "Enter database name: " DATABASE_NAME
echo "Write your password in PostgreSQL"
dropdb -h localhost -p 5432 -U postgres --if-exists "$DATABASE_NAME"
echo "Write your password in PostgreSQL"
createdb -h localhost -p 5432 -U postgres "$DATABASE_NAME"
echo "Write your password in UNIX"
sudo su postgres -c "psql -U postgres -d $DATABASE_NAME -a -q -f $PROJECT_FOLDER_PATH/setup_database.sql" 1> /dev/null
sed -i -e "s/DATABASE_NAME/$DATABASE_NAME/g" "$PROJECT_FOLDER_PATH/config.py"

echo "CREATING VIRTUAL ENVIRONMENT"
rm -rf "$PROJECT_FOLDER_PATH/venv"
python3 -m venv "$PROJECT_FOLDER_PATH/venv"


echo "INSTALLING PACKAGES"
"$PROJECT_INTERPRETER_PATH" -m pip install -U pip -U setuptools 1> /dev/null
"$PROJECT_INTERPRETER_PATH" -m pip install -U wheel 1> /dev/null
"$PROJECT_INTERPRETER_PATH" -m pip install -r requirements.txt 1> /dev/null
