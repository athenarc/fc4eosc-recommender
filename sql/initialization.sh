# Ensure that the file has the right permissions (chmod +x initialization.sh)
# Usage: ./initialization.sh <host> <port> <user> <password> <database>

### Add sk_ids for query optmization reasons
PGPASSWORD=$4 psql --host=$1 --port=$2 --username=$3 --dbname=$5 -a -f add_sk_ids.sql

## Build extra indexes
PGPASSWORD=$4 psql --host=$1 --port=$2 --username=$3 --dbname=$5 -a -f build_extra_indexes.sql

## Create recommenders schema
PGPASSWORD=$4 psql --host=$1 --port=$2 --username=$3 --dbname=$5 -a -f build_recommenders_schema.sql
