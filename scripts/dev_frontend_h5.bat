@echo off
setlocal
cd /d "%~dp0\..\frontend"
echo Starting frontend H5 dev server
npm run dev:h5
