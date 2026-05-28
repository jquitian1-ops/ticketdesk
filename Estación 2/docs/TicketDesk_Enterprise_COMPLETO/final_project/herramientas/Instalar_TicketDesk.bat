@echo off
title TicketDesk Enterprise — Instalador Windows Server
color 0A
setlocal enabledelayedexpansion

echo.
echo  ============================================================
echo   TicketDesk Enterprise v2.0 — Instalador Windows Server
echo   Manufacturas Eliot
echo  ============================================================
echo.

:: ── Verificar que se ejecuta como Administrador ──────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Este script debe ejecutarse como Administrador.
    echo  Clic derecho en el archivo ^> Ejecutar como administrador
    pause & exit /b 1
)

:: ── Variables ────────────────────────────────────────────────
set INSTDIR=C:\TicketDesk
set PORTDIR=%INSTDIR%\portales
set LOGFILE=%INSTDIR%\install.log
set PORT=5050

echo  [1/8] Creando carpetas...
if not exist "%INSTDIR%" mkdir "%INSTDIR%"
if not exist "%PORTDIR%" mkdir "%PORTDIR%"
echo        OK: %INSTDIR%
echo        OK: %PORTDIR%

:: ── Verificar Python ─────────────────────────────────────────
echo.
echo  [2/8] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [AVISO] Python no encontrado.
    echo  Descarga Python 3.11 desde: https://www.python.org/downloads/windows/
    echo  Marca "Add Python to PATH" durante la instalacion.
    echo.
    set /p OPEN_PY="Abrir python.org ahora? (s/n): "
    if /i "!OPEN_PY!"=="s" start https://www.python.org/downloads/windows/
    echo  Vuelve a ejecutar este script despues de instalar Python.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo        OK: %%v

:: ── Copiar archivos del sistema ──────────────────────────────
echo.
echo  [3/8] Copiando archivos del sistema...
set SCRIPT_DIR=%~dp0

for %%f in (server_enterprise.py api_client.js database.py ldap_bridge.py) do (
    if exist "%SCRIPT_DIR%%%f" (
        copy /y "%SCRIPT_DIR%%%f" "%INSTDIR%\%%f" >nul
        echo        Copiado: %%f
    ) else (
        echo        [AVISO] No encontrado: %%f
    )
)

:: Portales HTML
for %%f in (gestion_tickets_v2.html portal_usuarios.html portal_especialista.html) do (
    if exist "%SCRIPT_DIR%%%f" (
        copy /y "%SCRIPT_DIR%%%f" "%PORTDIR%\%%f" >nul
        copy /y "%SCRIPT_DIR%%%f" "%INSTDIR%\%%f" >nul
        echo        Copiado: %%f
    )
)

:: ── Crear .env si no existe ───────────────────────────────────
echo.
echo  [4/8] Configurando archivo .env...
if not exist "%INSTDIR%\.env" (
    :: Generar clave aleatoria simple
    set RKEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%
    (
        echo JWT_SECRET=TicketDesk_!RKEY!_CambiaEsto
        echo DB_PATH=C:\TicketDesk\ticketdesk.db
        echo PORT=%PORT%
    ) > "%INSTDIR%\.env"
    echo        Creado: %INSTDIR%\.env
    echo        [IMPORTANTE] Edita la clave JWT_SECRET en %INSTDIR%\.env
) else (
    echo        Ya existe: %INSTDIR%\.env
)

:: ── Instalar dependencias Python ──────────────────────────────
echo.
echo  [5/8] Instalando dependencias Python...
echo        (esto puede tardar 1-2 minutos)
pip install flask flask-cors flask-socketio python-dotenv ldap3 requests eventlet --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] Fallo al instalar dependencias. Verifica la conexion a internet.
    pause & exit /b 1
)
echo        OK: flask, flask-cors, flask-socketio, ldap3, eventlet

:: ── Abrir puerto en firewall ──────────────────────────────────
echo.
echo  [6/8] Configurando firewall (puerto %PORT%)...
netsh advfirewall firewall add rule name="TicketDesk API" protocol=TCP dir=in localport=%PORT% action=allow >nul 2>&1
netsh advfirewall firewall add rule name="TicketDesk API OUT" protocol=TCP dir=out localport=%PORT% action=allow >nul 2>&1
echo        OK: Puerto %PORT% abierto en Windows Firewall

:: ── Compartir carpeta de portales ─────────────────────────────
echo.
echo  [7/8] Compartiendo carpeta de portales en red...
net share TicketDesk="%PORTDIR%" /grant:Everyone,READ >nul 2>&1
if %errorlevel% equ 0 (
    echo        OK: \\%COMPUTERNAME%\TicketDesk compartido
) else (
    echo        [INFO] El recurso compartido ya existe o requiere configuracion manual
)

:: ── Instalar como servicio de Windows ────────────────────────
echo.
echo  [8/8] Instalando servicio de Windows...

:: Buscar NSSM
set NSSM_PATH=
if exist "%INSTDIR%\nssm.exe"       set NSSM_PATH=%INSTDIR%\nssm.exe
if exist "%~dp0nssm.exe"            set NSSM_PATH=%~dp0nssm.exe
if exist "C:\Windows\nssm.exe"      set NSSM_PATH=C:\Windows\nssm.exe

if "!NSSM_PATH!"=="" (
    echo        [AVISO] nssm.exe no encontrado — instalando servicio manual...
    
    :: Crear script de inicio alternativo
    (
        echo @echo off
        echo cd /d C:\TicketDesk
        echo python server_enterprise.py ^> C:\TicketDesk\ticketdesk.log 2^>^&1
    ) > "%INSTDIR%\Iniciar_Servidor.bat"
    
    :: Registrar en inicio de Windows via registro
    reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "TicketDesk" /t REG_SZ /d "C:\TicketDesk\Iniciar_Servidor.bat" /f >nul 2>&1
    echo        Registrado en inicio de Windows (sin NSSM)
    echo        [INFO] Para mejor gestion, descarga nssm.exe desde https://nssm.cc
    goto :iniciar
)

:: Instalar con NSSM
!NSSM_PATH! stop TicketDesk >nul 2>&1
!NSSM_PATH! remove TicketDesk confirm >nul 2>&1
for /f "tokens=*" %%p in ('where python') do set PYTHON_PATH=%%p
!NSSM_PATH! install TicketDesk "!PYTHON_PATH!" >nul 2>&1
!NSSM_PATH! set TicketDesk AppDirectory "%INSTDIR%" >nul 2>&1
!NSSM_PATH! set TicketDesk AppParameters "server_enterprise.py" >nul 2>&1
!NSSM_PATH! set TicketDesk AppStdout "%INSTDIR%\ticketdesk.log" >nul 2>&1
!NSSM_PATH! set TicketDesk AppStderr "%INSTDIR%\ticketdesk_err.log" >nul 2>&1
!NSSM_PATH! set TicketDesk Start SERVICE_AUTO_START >nul 2>&1
echo        OK: Servicio TicketDesk instalado con NSSM

:iniciar
:: ── Iniciar servidor ──────────────────────────────────────────
echo.
echo  Iniciando servidor TicketDesk...
if "!NSSM_PATH!"=="" (
    start "TicketDesk Server" /MIN cmd /c "%INSTDIR%\Iniciar_Servidor.bat"
) else (
    !NSSM_PATH! start TicketDesk >nul 2>&1
)

:: Esperar y verificar
timeout /t 4 /nobreak >nul
curl -s http://localhost:%PORT%/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Servidor funcionando en http://localhost:%PORT%
) else (
    echo  [INFO] El servidor esta iniciando, puede tardar unos segundos...
    echo  Verifica con: curl http://localhost:%PORT%/api/health
)

:: ── Crear accesos directos ────────────────────────────────────
echo.
echo  Creando accesos directos en el escritorio...

powershell -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%PUBLIC%\Desktop\TicketDesk Admin.lnk'); $s.TargetPath='%PORTDIR%\gestion_tickets_v2.html'; $s.Description='TicketDesk Sistema Principal'; $s.Save()" >nul 2>&1
powershell -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%PUBLIC%\Desktop\TicketDesk Especialista.lnk'); $s.TargetPath='%PORTDIR%\portal_especialista.html'; $s.Description='TicketDesk Portal Especialista'; $s.Save()" >nul 2>&1

echo  ============================================================
echo.
echo   INSTALACION COMPLETADA
echo.
echo   Servidor API:     http://localhost:%PORT%
echo   Portal Admin:     %PORTDIR%\gestion_tickets_v2.html  
echo   Portal Usuarios:  \\%COMPUTERNAME%\TicketDesk\portal_usuarios.html
echo.
echo   SIGUIENTE PASO:
echo   Edita C:\TicketDesk\.env y cambia JWT_SECRET
echo   Luego reinicia el servicio:
echo   nssm.exe restart TicketDesk
echo.
echo  ============================================================
echo.
echo  Presiona cualquier tecla para abrir el sistema principal...
pause >nul
start "" "%PORTDIR%\gestion_tickets_v2.html"
