@echo off
REM Stop the local dev Postgres cluster.
set HERE=%~dp0
set PGBIN=%HERE%..\.pgdev\pgsql\bin
set PGDATA=%HERE%..\.pgdev\data
"%PGBIN%\pg_ctl" -D "%PGDATA%" stop
