@echo off
REM Atalho para rodar o Twygo QA App sem precisar ativar o venv manualmente.
REM Uso: duplo-clique no arquivo, ou `.\run.cmd` no PowerShell.

"%~dp0.venv\Scripts\python.exe" -m app.main %*
