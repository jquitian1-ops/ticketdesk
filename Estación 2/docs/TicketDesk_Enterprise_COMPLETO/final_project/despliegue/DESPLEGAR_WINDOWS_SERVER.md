# TicketDesk Enterprise — Despliegue en Windows Server

## Resumen
- **Servidor:** Windows Server 2016/2019/2022
- **Acceso:** IP interna (192.168.x.x) + nombre de dominio interno
- **Capacidad:** 100+ técnicos TI / 8,000+ empleados simultáneos
- **Tiempo estimado de instalación:** 30-45 minutos

---

## PASO 1 — Instalar Python 3.11

1. Descarga Python desde: https://www.python.org/downloads/windows/
   - Versión recomendada: **Python 3.11.x (64-bit)**
2. Ejecuta el instalador como **Administrador**
3. Marca la casilla **"Add Python to PATH"** antes de instalar
4. Verifica la instalación:
   ```cmd
   python --version
   ```
   Debe mostrar: `Python 3.11.x`

---

## PASO 2 — Crear la carpeta del sistema

```cmd
mkdir C:\TicketDesk
```

Copia estos archivos a `C:\TicketDesk\`:
```
C:\TicketDesk\
├── server_enterprise.py
├── api_client.js
├── database.py
├── gestion_tickets_v2.html
├── portal_usuarios.html
├── portal_especialista.html
├── .env
└── portales\           ← carpeta compartida en red (ver Paso 5)
```

---

## PASO 3 — Instalar dependencias Python

Abre **CMD como Administrador** y ejecuta:

```cmd
cd C:\TicketDesk
pip install flask flask-cors flask-socketio python-dotenv ldap3 requests eventlet
```

Espera a que termine (descarga ~15 MB).

---

## PASO 4 — Configurar el archivo .env

Crea el archivo `C:\TicketDesk\.env` con este contenido:

```env
# ─── OBLIGATORIO — cambia esta clave ───────────────
JWT_SECRET=CAMBIA_ESTA_CLAVE_LARGA_Y_SEGURA_2026

# ─── Base de datos ──────────────────────────────────
DB_PATH=C:\TicketDesk\ticketdesk.db

# ─── Puerto del servidor ────────────────────────────
PORT=5050

# ─── URL pública (para los portales HTML) ───────────
# Pon la IP interna del servidor:
SERVER_URL=http://192.168.1.100:5050
# Si tienes nombre de dominio interno, usa también:
# SERVER_URL=http://ticketdesk.empresa.local:5050
```

> **IMPORTANTE:** Cambia `JWT_SECRET` por una cadena larga y aleatoria.
> Ejemplo: `JWT_SECRET=xK9$mP2#vL7@nQ4&wR8!tY3*uO6^hJ1`

---

## PASO 5 — Compartir la carpeta de portales en red

Para que los 8,000 empleados accedan a los HTML:

1. Crea la carpeta: `C:\TicketDesk\portales\`
2. Copia los 3 archivos HTML dentro:
   - `portal_usuarios.html`
   - `gestion_tickets_v2.html`
   - `portal_especialista.html`
3. Comparte la carpeta en red:
   - Clic derecho en `C:\TicketDesk\portales\`
   - **Propiedades → Compartir → Uso compartido avanzado**
   - Marca **"Compartir esta carpeta"**
   - Nombre del recurso: `TicketDesk`
   - Permisos: **Todos → Lectura**
4. Los empleados acceden así:
   ```
   \\NOMBRE_SERVIDOR\TicketDesk\portal_usuarios.html
   ```
   O si tienes DNS interno:
   ```
   \\ticketdesk.empresa.local\portal_usuarios.html
   ```

---

## PASO 6 — Abrir el puerto 5050 en el firewall

Abre **CMD como Administrador**:

```cmd
netsh advfirewall firewall add rule name="TicketDesk API" protocol=TCP dir=in localport=5050 action=allow
netsh advfirewall firewall add rule name="TicketDesk API OUT" protocol=TCP dir=out localport=5050 action=allow
```

---

## PASO 7 — Instalar como servicio de Windows (NSSM)

Para que el servidor arranque automáticamente con Windows:

### 7a. Descargar NSSM
Descarga desde: https://nssm.cc/download
Extrae `nssm.exe` a `C:\TicketDesk\nssm.exe`

### 7b. Instalar el servicio

```cmd
cd C:\TicketDesk
nssm.exe install TicketDesk
```

En la ventana que aparece:
- **Path:** `C:\Python311\python.exe` (o donde esté Python)
- **Startup directory:** `C:\TicketDesk`
- **Arguments:** `server_enterprise.py`
- Pestaña **Environment:** `PATH=C:\Python311;C:\Python311\Scripts`

### 7c. Iniciar el servicio

```cmd
nssm.exe start TicketDesk
```

### 7d. Verificar que funciona

```cmd
curl http://localhost:5050/api/health
```

Debe responder:
```json
{"status":"ok","db":true,"version":"2.0-enterprise","capacity":"100+ técnicos / 8000+ usuarios"}
```

---

## PASO 8 — Verificar acceso desde la red

Desde otra PC de la red:

```
http://192.168.1.100:5050/api/health
```

Si tienes DNS interno configurado:
```
http://ticketdesk.empresa.local:5050/api/health
```

---

## PASO 9 — Crear usuario administrador inicial

Desde cualquier PC con acceso al servidor:

```cmd
curl -X POST http://192.168.1.100:5050/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"tu_password_admin\",\"company_id\":\"me\"}"
```

Copia el `token` de la respuesta y crea los primeros usuarios:

```cmd
curl -X POST http://192.168.1.100:5050/api/users ^
  -H "Authorization: Bearer TOKEN_AQUI" ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"jgarcia\",\"display_name\":\"Juan Garcia\",\"role\":\"agent\",\"company_id\":\"me\",\"password\":\"Pass123!\"}"
```

---

## PASO 10 — Distribuir a empleados

### Opción A — Carpeta de red (recomendada)
Envía este mensaje a los empleados por correo o Teams:

> Para abrir el sistema de tickets ve a:
> `\\NOMBRE_SERVIDOR\TicketDesk\portal_usuarios.html`
> 
> La primera vez te pedirá configurar el servidor:
> Escribe: `http://192.168.1.100:5050` y haz clic en Verificar.

### Opción B — Acceso directo en el escritorio (via GPO)
Si tienes Active Directory, puedes crear un acceso directo por Política de Grupo apuntando a:
```
\\NOMBRE_SERVIDOR\TicketDesk\portal_usuarios.html
```

---

## Comandos de gestión del servicio

```cmd
nssm.exe start TicketDesk      ← iniciar
nssm.exe stop TicketDesk       ← detener
nssm.exe restart TicketDesk    ← reiniciar
nssm.exe status TicketDesk     ← ver estado
```

Ver logs del servidor:
```cmd
type C:\TicketDesk\ticketdesk.log
```

---

## Troubleshooting común

| Problema | Solución |
|---|---|
| `pip` no se reconoce | Reinstala Python marcando "Add to PATH" |
| Puerto 5050 no accesible | Verifica el firewall con `netstat -an \| find "5050"` |
| Error "address in use" | Hay otro proceso en el puerto: `netstat -ano \| find "5050"` |
| HTML no conecta al servidor | Verifica que la URL en el campo del servidor sea correcta |
| Empleados no ven la carpeta compartida | Verifica permisos de red en la carpeta |

---

## Arquitectura final

```
[8,000 empleados]
\\servidor\TicketDesk\portal_usuarios.html
          │
          ▼
[Servidor Windows Server]          [100 técnicos TI]
server_enterprise.py :5050  ◄───── gestion_tickets_v2.html
          │                         portal_especialista.html
          ▼
   ticketdesk.db (SQLite WAL)
   C:\TicketDesk\ticketdesk.db
```

