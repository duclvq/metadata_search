@echo off
echo === Copying latest source code ===
xcopy /E /Y /I ..\..\api api
xcopy /E /Y /I ..\..\src src
xcopy /E /Y /I ..\..\scripts scripts

echo === Building Docker image ===
docker compose up -d --build

echo === Cleaning up copied source ===
rmdir /S /Q api src scripts

echo === Done ===
docker compose ps
