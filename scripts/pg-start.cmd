@echo off
REM Start the local dev Postgres cluster on port 5433.
set HERE=%~dp0
set PGBIN=%HERE%..\.pgdev\pgsql\bin
set PGDATA=%HERE%..\.pgdev\data
"%PGBIN%\pg_ctl" -D "%PGDATA%" -o "-p 5433" -l "%HERE%..\.pgdev\pg.log" start
