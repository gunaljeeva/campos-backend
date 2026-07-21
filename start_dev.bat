@echo off
cd /d C:\Users\fi_gu\pws\campos\backend
copy /y .env.dev .env.current >nul
venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --env-file .env.dev
