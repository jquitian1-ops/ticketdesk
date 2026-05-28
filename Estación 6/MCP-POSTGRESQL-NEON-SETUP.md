# 🗄️ MCP: PostgreSQL/Neon Integration para TicketDesk

**Protocol**: Model Context Protocol  
**Database**: PostgreSQL 15 (Neon serverless)  
**Propósito**: Acceso estructurado a base de datos desde agentes  
**Herramientas**: Queries, Migrations, Schema Inspection  
**Fecha**: 2026-05-27

---

## Resumen

El MCP de PostgreSQL permite a los agentes:
- ✅ Ejecutar queries SELECT/INSERT/UPDATE/DELETE
- ✅ Inspeccionar schema (tablas, índices, constraints)
- ✅ Ejecutar migraciones (Alembic)
- ✅ Validar data integrity
- ✅ Monitorear performance
- ✅ Generar documentación (SCHEMA.md)

---

## Setup: Local + Neon

### Opción 1: Local PostgreSQL (Desarrollo)

```bash
# Instalar PostgreSQL 15
brew install postgresql@15

# Iniciar servidor
brew services start postgresql@15

# Crear base de datos
createdb ticketdesk_dev

# Crear usuario
createuser ticketdesk_user
psql -d ticketdesk_dev -c "ALTER USER ticketdesk_user WITH PASSWORD 'dev_password';"
psql -d ticketdesk_dev -c "GRANT ALL PRIVILEGES ON DATABASE ticketdesk_dev TO ticketdesk_user;"

# .env local
DATABASE_URL=postgresql://ticketdesk_user:dev_password@localhost:5432/ticketdesk_dev
```

### Opción 2: Neon (Producción/Staging)

```bash
# 1. Crear cuenta en https://console.neon.tech
# 2. Crear proyecto "TicketDesk"
# 3. Copiar connection string:

NEON_DATABASE_URL=postgresql://user:password@ep-xxxxx.us-east-1.neon.tech/ticketdesk?sslmode=require

# 4. Guardar en .env (nunca en git)
echo "DATABASE_URL=$NEON_DATABASE_URL" >> .env
```

---

## Configuración MCP (settings.json)

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres"
      ],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/ticketdesk_dev",
        "SSL_MODE": "disable"  // "require" for Neon
      }
    }
  }
}
```

---

## Herramientas Disponibles

### 1. Ejecutar Query

```python
# SELECT
result = execute_query("""
    SELECT id, email, role, created_at
    FROM users
    WHERE role = 'admin'
    ORDER BY created_at DESC
    LIMIT 10
""")

print(result)
# Output: [(uuid, email, 'admin', datetime), ...]

# INSERT
execute_query("""
    INSERT INTO users (id, email, password_hash, role, created_at)
    VALUES (%s, %s, %s, %s, %s)
""", [user_id, email, password_hash, 'candidate', datetime.now()])

# UPDATE
execute_query("""
    UPDATE sessions
    SET status = %s, updated_at = %s
    WHERE id = %s
""", ['evaluated', datetime.now(), session_id])

# DELETE (soft-delete for LGPD)
execute_query("""
    UPDATE users
    SET deleted_at = %s
    WHERE id = %s
""", [datetime.now(), user_id])
```

### 2. Inspeccionar Schema

```python
# Get all tables
tables = get_tables()
# Output: ['users', 'roles', 'sessions', 'audit_logs', ...]

# Get table structure
schema = get_table_schema('sessions')
print(schema)
# Output:
# {
#   'columns': [
#     {'name': 'id', 'type': 'uuid', 'null': False, 'pk': True},
#     {'name': 'account_id', 'type': 'uuid', 'null': False, 'fk': 'users.id'},
#     {'name': 'status', 'type': 'varchar', 'null': False},
#     {'name': 'deleted_at', 'type': 'timestamp', 'null': True},
#   ],
#   'indexes': [
#     {'name': 'account_id_idx', 'columns': ['account_id']},
#   ]
# }

# Validate schema against models
if not validate_schema_matches_models('sessions', Session):
    print("⚠️ Schema mismatch detected")
```

### 3. Ejecutar Migraciones

```python
# List pending migrations
pending = get_pending_migrations()
print(pending)
# Output: ['002_user_aggregate.py', '003_session_management.py']

# Apply migrations
apply_migrations()
# Output: 
# ✅ Applied: 001_initial_schema.py
# ✅ Applied: 002_user_aggregate.py

# Rollback last migration
rollback_migration()
# Output: Rolled back: 002_user_aggregate.py

# Run specific migration
run_migration('003_session_management.py')
```

### 4. Data Validation

```python
# Check LGPD compliance (soft-delete SLA)
def check_lgpd_soft_delete_sla():
    """Verify deleted users are hard-deleted within 24h"""
    
    # Get soft-deleted users older than 24h
    old_soft_deleted = execute_query("""
        SELECT id, email, deleted_at
        FROM users
        WHERE deleted_at IS NOT NULL
        AND deleted_at < NOW() - INTERVAL '24 hours'
    """)
    
    if old_soft_deleted:
        print(f"❌ LGPD SLA violation: {len(old_soft_deleted)} users not hard-deleted")
        # Trigger hard-delete for these users
        hard_delete_users([user[0] for user in old_soft_deleted])
    else:
        print("✅ LGPD SLA compliant")

# Run validation
check_lgpd_soft_delete_sla()
```

### 5. Performance Monitoring

```python
# Get slow queries
slow_queries = execute_query("""
    SELECT query, calls, mean_time, max_time
    FROM pg_stat_statements
    WHERE mean_time > 100  -- > 100ms
    ORDER BY mean_time DESC
    LIMIT 10
""")

# Get table sizes
table_sizes = execute_query("""
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
""")

# Get index usage
unused_indexes = execute_query("""
    SELECT schemaname, tablename, indexname
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0
    ORDER BY idx_blks_read DESC
""")
```

### 6. Generate SCHEMA.md

```python
def generate_schema_documentation():
    """Auto-generate SCHEMA.md from actual schema"""
    
    doc = "# Database Schema — TicketDesk Enterprise\n\n"
    doc += f"**Generated**: {datetime.now().isoformat()}\n\n"
    
    for table_name in get_tables():
        schema = get_table_schema(table_name)
        doc += f"## {table_name} table\n\n"
        
        # Columns table
        doc += "| Column | Type | Constraints | Notes |\n"
        doc += "|--------|------|-------------|-------|\n"
        for col in schema['columns']:
            constraints = []
            if col['pk']: constraints.append("PRIMARY KEY")
            if col['unique']: constraints.append("UNIQUE")
            if not col['null']: constraints.append("NOT NULL")
            if col['fk']: constraints.append(f"FK → {col['fk']}")
            
            doc += f"| {col['name']} | {col['type']} | {', '.join(constraints)} | |\n"
        
        doc += "\n"
    
    # Write to file
    with open("docs/SCHEMA.md", "w") as f:
        f.write(doc)
    
    return doc

generate_schema_documentation()
```

---

## Flujo de Ejecución Semana 1

### ENGINEER-1: T1.1 (Database Schema)

```python
# LUNES 27-MAY
# 1. Lee task 001-T1.1-database-schema.md
# 2. Crea migration

from mcp_postgresql import apply_migrations, validate_schema

# Crear migration file
create_migration("""
    CREATE TABLE users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'recruiter', 'candidate')),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE TABLE sessions (
        id UUID PRIMARY KEY,
        account_id UUID NOT NULL REFERENCES users(id),
        candidate_email VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        deleted_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE TABLE audit_logs (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL REFERENCES users(id),
        action VARCHAR(50) NOT NULL,
        resource VARCHAR(50) NOT NULL,
        resource_id UUID NOT NULL,
        changes JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX users_email_idx ON users(email);
    CREATE INDEX sessions_account_id_idx ON sessions(account_id);
    CREATE INDEX audit_logs_user_id_idx ON audit_logs(user_id);
""")

# 3. Apply migration
apply_migrations()

# ✅ Output:
# Applied migration: 001_initial_schema.py
# Tables created: 3
# Indexes created: 3

# 4. Validate
if validate_schema_matches_design("DESIGN.md"):
    print("✅ Schema matches DESIGN.md requirements")

# 5. Generate docs
generate_schema_documentation()
# ✅ Generated: docs/SCHEMA.md

# 6. Run tests
execute_query("SELECT COUNT(*) FROM users WHERE deleted_at IS NULL")
# Output: 0 (expected for new database)
```

### ENGINEER-1: T1.2 (User Aggregate)

```python
# MARTES 28-MAY
# Después de T1.1 migration aplicada

# Test User creation
from mcp_postgresql import execute_query
import bcrypt

email = "test@example.com"
password = "secure_password"
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

execute_query("""
    INSERT INTO users (id, email, password_hash, role)
    VALUES (%s, %s, %s, %s)
""", [uuid4(), email, password_hash, 'candidate'])

# Verify insert
result = execute_query("""
    SELECT id, email, role FROM users WHERE email = %s
""", [email])

assert result, "User creation failed"
print(f"✅ User created: {result[0]}")

# Test duplicate email constraint
try:
    execute_query("""
        INSERT INTO users (id, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """, [uuid4(), email, password_hash, 'candidate'])
    print("❌ Duplicate email should be rejected")
except psycopg2.IntegrityError:
    print("✅ Duplicate email correctly rejected")
```

---

## Configuración para Neon (Producción/Staging)

### Environment Variables

```bash
# .env.staging
DATABASE_URL=postgresql://ticketdesk_user:PASSWORD@ep-xxxxx-staging.us-east-1.neon.tech/ticketdesk_staging?sslmode=require
DATABASE_SSL=true
DATABASE_POOL_SIZE=20

# .env.production  
DATABASE_URL=postgresql://ticketdesk_user:PASSWORD@ep-xxxxx-prod.us-east-1.neon.tech/ticketdesk?sslmode=require
DATABASE_SSL=true
DATABASE_POOL_SIZE=50
```

### Neon Dashboard Monitoring

```
https://console.neon.tech/

Monitoring:
├─ Query latency (P50, P95, P99)
├─ Active connections
├─ Database size
├─ Backup status (automated daily)
└─ Scale compute (auto-scaling available)
```

---

## Seguridad & Compliance

### LGPD Hard-Delete Worker

```python
# Celery task para hard-delete automático
@celery_app.task
def hard_delete_old_soft_deleted_users():
    """
    LGPD requirement: Hard-delete users 24h after soft-delete
    """
    old_deleted = execute_query("""
        SELECT id FROM users
        WHERE deleted_at IS NOT NULL
        AND deleted_at < NOW() - INTERVAL '24 hours'
    """)
    
    for user_id in old_deleted:
        # Delete all PII and references
        execute_query("DELETE FROM audit_logs WHERE user_id = %s", [user_id])
        execute_query("DELETE FROM sessions WHERE account_id = %s", [user_id])
        execute_query("DELETE FROM users WHERE id = %s", [user_id])
        
        print(f"✅ Hard-deleted user {user_id}")

# Schedule: every hour
celery_beat_schedule = {
    'hard-delete-old-users': {
        'task': 'tasks.hard_delete_old_soft_deleted_users',
        'schedule': crontab(minute=0),  # Every hour
    }
}
```

### PII Protection in Logs

```python
# Mask sensitive data in query logs
def mask_pii_in_logs(query, params):
    """Never log email, passwords, or sensitive data"""
    
    masked_query = query
    masked_params = []
    
    for param in params:
        if is_email(param) or is_password(param):
            masked_params.append("***MASKED***")
        else:
            masked_params.append(param)
    
    return masked_query, masked_params

# All queries logged via this function
execute_query = masked_execute_query
```

---

## Testing with MCP PostgreSQL

```bash
# Health check
claude-code --test-mcp postgresql

# Expected:
# ✅ PostgreSQL connected
# ✅ Database: ticketdesk_dev
# ✅ Tables: 0 (fresh database)

# Run migration test
python scripts/test_migrations.py

# Expected:
# ✅ Migration 001_initial_schema applied
# ✅ 3 tables created
# ✅ 3 indexes created

# Validate schema
python scripts/validate_schema.py

# Expected:
# ✅ Schema matches DESIGN.md
# ✅ All constraints present
# ✅ All indexes created
```

---

## Status: ✅ MCP PostgreSQL/Neon Ready

**Local**: Configurado para desarrollo  
**Staging**: Neon setup pending (antes de Semana 3)  
**Production**: Neon setup pending (antes de Semana 4)
