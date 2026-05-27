#!/usr/bin/env sh
set -eu

psql_base() {
  psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -v ON_ERROR_STOP=1 "$@"
}

psql_base \
  -v prefect_db="${PREFECT_DB_NAME:-prefect}" \
  -v prefect_user="${PREFECT_DB_USER:-prefect}" \
  -v prefect_password="${PREFECT_DB_PASSWORD:-prefect}" \
  -v scheduler_db="${AGENT_SCHEDULER_DB_NAME:-agent_scheduler}" \
  -v scheduler_user="${AGENT_SCHEDULER_DB_USER:-agent_scheduler_app}" \
  -v scheduler_password="${AGENT_SCHEDULER_DB_PASSWORD:-agent_scheduler}" \
  -v pipeline_db="${PIPELINE_DB_NAME:-pipeline_data}" \
  -v pipeline_user="${PIPELINE_DB_USER:-pipeline_app}" \
  -v pipeline_password="${PIPELINE_DB_PASSWORD:-pipeline_app}" \
  -v trading_user="${TRADING_PRIVATE_DB_USER:-trading_private_writer}" \
  -v trading_password="${TRADING_PRIVATE_DB_PASSWORD:-trading_private}" \
  -v analytics_user="${ANALYTICS_DB_USER:-analytics_reader}" \
  -v analytics_password="${ANALYTICS_DB_PASSWORD:-analytics_reader}" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'prefect_user', :'prefect_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'prefect_user') \gexec
SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'prefect_user', :'prefect_password') \gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'scheduler_user', :'scheduler_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'scheduler_user') \gexec
SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'scheduler_user', :'scheduler_password') \gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'pipeline_user', :'pipeline_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'pipeline_user') \gexec
SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'pipeline_user', :'pipeline_password') \gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'trading_user', :'trading_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'trading_user') \gexec
SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'trading_user', :'trading_password') \gexec

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'analytics_user', :'analytics_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'analytics_user') \gexec
SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'analytics_user', :'analytics_password') \gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'prefect_db', :'prefect_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'prefect_db') \gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'scheduler_db', :'scheduler_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'scheduler_db') \gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'pipeline_db', :'pipeline_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'pipeline_db') \gexec
SQL

psql --username "$POSTGRES_USER" --dbname "${AGENT_SCHEDULER_DB_NAME:-agent_scheduler}" -v ON_ERROR_STOP=1 \
  -v scheduler_user="${AGENT_SCHEDULER_DB_USER:-agent_scheduler_app}" \
  -v analytics_user="${ANALYTICS_DB_USER:-analytics_reader}" <<'SQL'
CREATE SCHEMA IF NOT EXISTS scheduler_app;
ALTER SCHEMA scheduler_app OWNER TO :"scheduler_user";

REVOKE ALL ON SCHEMA public FROM PUBLIC;
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'scheduler_user') \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'analytics_user') \gexec
GRANT USAGE, CREATE ON SCHEMA scheduler_app TO :"scheduler_user";
GRANT USAGE ON SCHEMA scheduler_app TO :"analytics_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"scheduler_user" IN SCHEMA scheduler_app
  GRANT SELECT ON TABLES TO :"analytics_user";
SQL

psql --username "$POSTGRES_USER" --dbname "${PIPELINE_DB_NAME:-pipeline_data}" -v ON_ERROR_STOP=1 \
  -v pipeline_user="${PIPELINE_DB_USER:-pipeline_app}" \
  -v trading_user="${TRADING_PRIVATE_DB_USER:-trading_private_writer}" \
  -v analytics_user="${ANALYTICS_DB_USER:-analytics_reader}" <<'SQL'
CREATE SCHEMA IF NOT EXISTS pipeline_app;
CREATE SCHEMA IF NOT EXISTS public_data;
CREATE SCHEMA IF NOT EXISTS trading_private;

ALTER SCHEMA pipeline_app OWNER TO :"pipeline_user";
ALTER SCHEMA public_data OWNER TO :"pipeline_user";
ALTER SCHEMA trading_private OWNER TO :"trading_user";

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA trading_private FROM PUBLIC;
REVOKE ALL ON SCHEMA trading_private FROM :"pipeline_user";
REVOKE ALL ON SCHEMA trading_private FROM :"analytics_user";

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'pipeline_user') \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'trading_user') \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'analytics_user') \gexec
GRANT USAGE, CREATE ON SCHEMA pipeline_app TO :"pipeline_user";
GRANT USAGE, CREATE ON SCHEMA public_data TO :"pipeline_user";
GRANT USAGE ON SCHEMA public_data TO :"trading_user", :"analytics_user";
GRANT USAGE, CREATE ON SCHEMA trading_private TO :"trading_user";
GRANT USAGE ON SCHEMA pipeline_app TO :"analytics_user";

ALTER DEFAULT PRIVILEGES FOR ROLE :"pipeline_user" IN SCHEMA public_data
  GRANT SELECT ON TABLES TO :"trading_user", :"analytics_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"pipeline_user" IN SCHEMA pipeline_app
  GRANT SELECT ON TABLES TO :"analytics_user";
SQL
