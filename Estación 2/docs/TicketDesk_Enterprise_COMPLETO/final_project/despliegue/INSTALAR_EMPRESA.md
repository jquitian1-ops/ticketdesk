# TicketDesk Enterprise — Guía de instalación para 100+ técnicos y 8,000 empleados

## Arquitectura recomendada

```
[8000 empleados]         [100 técnicos TI]
portal_usuarios.html --> servidor_api:5050 <-- gestion_tickets_v2.html
                                |                portal_especialista.html
                           [SQLite WAL]
                          ticketdesk.db
```

## Requisitos del servidor

- Windows Server 2019+ o Ubuntu 22.04+
- Python 3.10+
- RAM: 4 GB mínimo (8 GB recomendado)
- Disco: 10 GB mínimo para la base de datos
- Red: acceso desde todas las PCs de los empleados

## Instalación paso a paso

### 1. Instalar Python y dependencias

**Windows Server:**
```cmd
winget install Python.Python.3.11
pip install flask flask-cors flask-socketio python-dotenv ldap3 requests
```

**Linux:**
```bash
sudo apt install python3 python3-pip
pip3 install flask flask-cors flask-socketio python-dotenv ldap3 requests
```

### 2. Copiar archivos al servidor

Carpeta recomendada: `C:\TicketDesk\` (Windows) o `/opt/ticketdesk/` (Linux)

```
ticketdesk/
├── server_enterprise.py    ← servidor principal
├── api_client.js           ← cliente API (embebido en los HTML)
├── database.py             ← módulo SQLite
├── gestion_tickets_v2.html ← portal técnicos
├── portal_usuarios.html    ← portal empleados
├── portal_especialista.html← portal especialistas
└── .env                    ← configuración
```

### 3. Configurar el archivo .env

```env
JWT_SECRET=CAMBIA_ESTA_CLAVE_LARGA_Y_SEGURA_AQUI
DB_PATH=ticketdesk.db
PORT=5050
```

### 4. Iniciar el servidor

**Windows (como servicio):**
```cmd
python server_enterprise.py
```

Para que arranque automáticamente con Windows, usa NSSM:
```cmd
nssm install TicketDesk "C:\Python311\python.exe" "C:\TicketDesk\server_enterprise.py"
nssm set TicketDesk AppDirectory "C:\TicketDesk"
nssm start TicketDesk
```

**Linux (como servicio systemd):**
```bash
sudo nano /etc/systemd/system/ticketdesk.service
```
```ini
[Unit]
Description=TicketDesk Enterprise Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ticketdesk
ExecStart=/usr/bin/python3 /opt/ticketdesk/server_enterprise.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable ticketdesk
sudo systemctl start ticketdesk
```

### 5. Configurar los portales HTML

En cada portal, los empleados deben configurar la URL del servidor **una sola vez**:

1. Abrir el portal (doble clic en el HTML)
2. En la pantalla de login → campo "Servidor API"
3. Escribir: `http://IP-DEL-SERVIDOR:5050`
4. Guardar — el portal recuerda la URL

### 6. Abrir el puerto en el firewall

**Windows Server:**
```cmd
netsh advfirewall firewall add rule name="TicketDesk" protocol=TCP dir=in localport=5050 action=allow
```

**Linux:**
```bash
sudo ufw allow 5050/tcp
```

### 7. Crear usuarios iniciales

Via API (desde cualquier PC con curl o Postman):

```bash
# Login admin
curl -X POST http://SERVIDOR:5050/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"tu_password_admin","company_id":"me"}'

# Copiar el token JWT de la respuesta y crear usuarios:
curl -X POST http://SERVIDOR:5050/api/users \
  -H "Authorization: Bearer TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{"username":"jgarcia","display_name":"Juan García","role":"agent","company_id":"me","password":"password123"}'
```

## Capacidad y rendimiento

| Componente | Límite |
|---|---|
| Usuarios simultáneos | 500-1000 (con SQLite WAL) |
| Tickets en base de datos | Millones (SQLite soporta TB) |
| Escrituras concurrentes | ~100/seg sin bloqueo |
| Lecturas concurrentes | Sin límite práctico |
| WebSocket (tiempo real) | 1000 conexiones simultáneas |

## Escalar más allá de 1000 usuarios simultáneos

Si llegas a ese límite, migra a PostgreSQL:

```python
# En server_enterprise.py, cambiar SQLite por PostgreSQL:
pip install psycopg2-binary
# Cambiar get_db() para usar PostgreSQL
```

## Verificar que funciona

```bash
curl http://SERVIDOR:5050/api/health
# Respuesta: {"status":"ok","db":true,"version":"2.0-enterprise","capacity":"100+ técnicos / 8000+ usuarios"}
```

## Distribución a empleados

1. Comparte la carpeta del servidor por red: `\\SERVIDOR\TicketDesk\`
2. Los empleados abren `portal_usuarios.html` directamente desde la red
3. **O** copia los HTML a cada PC — configuran la URL del servidor una vez

Los técnicos usan `gestion_tickets_v2.html` (pueden tenerlo en su escritorio).

