@echo off
title TicketDesk — Configurar URL del Servidor
color 0B
echo.
echo  ============================================================
echo   TicketDesk — Configurar URL del Servidor en los Portales
echo  ============================================================
echo.

set PORTDIR=C:\TicketDesk\portales

:: Detectar IP del servidor automáticamente
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set DETECTED_IP=%%a
    set DETECTED_IP=!DETECTED_IP: =!
    goto :found_ip
)
:found_ip
echo  IP detectada de este servidor: %DETECTED_IP%
echo.
set /p SERVER_IP="Confirma la IP del servidor (Enter para usar %DETECTED_IP%): "
if "%SERVER_IP%"=="" set SERVER_IP=%DETECTED_IP%

set SERVER_URL=http://%SERVER_IP%:5050
echo  URL del servidor: %SERVER_URL%
echo.

:: Inyectar la URL como valor por defecto en los portales HTML
echo  Configurando portales...

for %%f in (gestion_tickets_v2.html portal_usuarios.html portal_especialista.html) do (
    if exist "%PORTDIR%\%%f" (
        powershell -Command "(Get-Content '%PORTDIR%\%%f') -replace \"localStorage.getItem\('tdv2_server'\) \|\| 'http://localhost:5050'\", \"localStorage.getItem\('tdv2_server'\) \|\| '%SERVER_URL%'\" | Set-Content '%PORTDIR%\%%f'"
        echo        OK: %%f configurado con %SERVER_URL%
    )
)

echo.
echo  Verifica que el servidor responde:
curl -s %SERVER_URL%/api/health
echo.
echo  LISTO. Los portales usaran %SERVER_URL% por defecto.
pause
