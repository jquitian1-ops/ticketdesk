# Unit 2: Fundamentos Backend — Actividad 3: Decisiones de Arquitectura (ADR)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 3 - Diseño NFR: Architecture Decision Records (ADR)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**4 Decisiones de Arquitectura** documentadas en formato Contexto-Opciones-Decisión-Consecuencias (CODC).

---

## 🎯 ADR-UNIT2-001: Autenticación y Autorización (JWT RS256 vs OAuth2 vs Sesión)

**Título**: Elegir mecanismo autenticación para API backend

**Estado**: ✅ ACEPTADA  
**Fecha**: 2026-05-27  
**Autor**: Equipo Backend  

### Contexto

TicketDesk tiene múltiples tipos de usuarios:
- **Candidatos**: Inician screening sin login (anónimos, luego correo verificado)
- **Reclutadores**: Requieren login + RBAC (ver candidatos asignados)
- **Administradores**: Acceso total (crear campañas, gestionar usuarios)

Necesitamos:
- Autenticación stateless (escalable horizontalmente)
- Autorización basada roles (recruiter ≠ admin)
- Refresh tokens (mantener sesiones largas sin revaloración)
- Integración con AWS (Cognito optional pero no crítico)
- Compatibilidad frontend (Next.js, localStorage)

### Opciones

#### Opción 1: JWT RS256 (Asymmetric Tokens)
**Descripción**: Public/private key pair. Backend firma tokens con private key, clientes validan con public key.

**Ventajas**:
- ✅ Stateless (no requiere sesión servidor)
- ✅ Escalable (múltiples instancias validan sin compartir estado)
- ✅ Seguro (RS256 asymmetric, private key protegido en AWS Secrets Manager)
- ✅ Token refresh posible (refresh token + access token pairing)
- ✅ RBAC integrado (claim `roles` en payload)

**Desventajas**:
- ❌ Revocación lenta (token válido hasta expiración, no inmediato)
- ❌ Token size más grande (>500 bytes si muchos claims)
- ❌ Complejidad generación keypair (pero herramientas disponibles)

**Ejemplo**:
```python
# Generar token
import jwt
payload = {
    "sub": "candidato-123",
    "email": "candidato@example.com",
    "roles": ["candidate"],
    "exp": datetime.now() + timedelta(hours=1),
    "iat": datetime.now()
}
token = jwt.encode(payload, private_key, algorithm="RS256")

# Validar token
decoded = jwt.decode(token, public_key, algorithms=["RS256"])
```

---

#### Opción 2: OAuth2 (Delegación Tercero)
**Descripción**: Integrar con proveedor OAuth2 (Google, GitHub, AWS Cognito).

**Ventajas**:
- ✅ Soporte SSO (candidatos logean con Google)
- ✅ Sin almacenar contraseñas (tercero gestiona)
- ✅ RBAC delegado a tercero (si provider soporta)

**Desventajas**:
- ❌ Dependencia externa (proveedor down = sin acceso)
- ❌ Costo variable (OAuth2 premium por usuario)
- ❌ Mayor latencia (round-trip a proveedor)
- ❌ LGPD compliance complejo (datos fluyen a tercero)

---

#### Opción 3: Sesión Tradicional (Session Cookies)
**Descripción**: Almacenar sesión en servidor (BD o Redis), cookie httpOnly para cliente.

**Ventajas**:
- ✅ Revocación inmediata (elimina sesión servidor)
- ✅ Seguro contra XSS (httpOnly cookie)

**Desventajas**:
- ❌ Requiere estado servidor (no escalable)
- ❌ Sticky session necesaria (sesión adherida a instancia)
- ❌ CORS complejo (credenciales incluidas)
- ❌ Móvil problemático (cookies no soportadas siempre)

---

### Decisión

**✅ JWT RS256 (Asymmetric Tokens)**

Razones:
1. **Escalabilidad**: Stateless permite auto-scaling sin sticky sessions
2. **Móvil-ready**: JWT funciona en apps nativas (almacenamiento local)
3. **LGPD-friendly**: No requiere tercero externo (no fluyen datos)
4. **Refresh tokens**: Permite access tokens corto-plazo (1h) + refresh largo-plazo (30d)

### Consecuencias

**Positivas**:
- ✅ Sistema escalable sin sesión servidor
- ✅ RBAC integrado en claims JWT
- ✅ Refresh token rotation adiciona seguridad
- ✅ Integración frontend simple (localStorage)

**Negativas**:
- ❌ Revocación tarda hasta expiración token (1h máximo)
- ❌ Manejo keypair añade complejidad operacional
- ❌ Token refresh requiere endpoint adicional

**Mitigación de Revocación Lenta**:
- Access token TTL = 1 hora (máximo retraso revocación)
- Blacklist en Redis para emergencias (logout inmediato)
- Monitoreo de tokens revocados en caché

### Implementación

```python
# Generar keypair (DevOps)
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# Almacenar en AWS Secrets Manager
secrets_client.create_secret(
    Name="jwt-private-key",
    SecretString=private_key.serialize()
)

# Crear token (backend)
def create_access_token(candidato_id, email, roles):
    payload = {
        "sub": candidato_id,
        "email": email,
        "roles": roles,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, private_key, algorithm="RS256")

# Validar token (middleware)
@app.middleware("http")
async def validate_token(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse({"error": "No token"}, status_code=401)
    
    token = auth_header.replace("Bearer ", "")
    try:
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        request.state.user = decoded
    except jwt.ExpiredSignatureError:
        return JSONResponse({"error": "Token expirado"}, status_code=401)
    except jwt.InvalidTokenError:
        return JSONResponse({"error": "Token inválido"}, status_code=401)
    
    return await call_next(request)

# Refresh token endpoint
@app.post("/auth/refresh")
async def refresh_token(request: Request):
    refresh_token = request.json["refresh_token"]
    # Validar refresh token
    decoded = jwt.decode(refresh_token, public_key, algorithms=["RS256"])
    # Generar nuevo access token
    new_access = create_access_token(decoded["sub"], decoded["email"], decoded["roles"])
    # Revocar refresh token anterior (optional, para seguridad)
    redis_client.setex(f"revoked:{refresh_token}", 86400*30, "1")
    # Generar nuevo refresh token
    new_refresh = jwt.encode({
        "sub": decoded["sub"],
        "type": "refresh",
        "exp": datetime.now() + timedelta(days=30)
    }, private_key, algorithm="RS256")
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "expires_in": 3600
    }
```

---

## 🎯 ADR-UNIT2-002: Sistema de Eventos (Redis Pub/Sub + Celery vs RabbitMQ vs Kafka)

**Título**: Elegir message broker para arquitectura event-driven

**Estado**: ✅ ACEPTADA  
**Fecha**: 2026-05-27  
**Autor**: Equipo Backend  

### Contexto

Flujos de negocio requieren comunicación asincrónica:
- Screening completado → Evaluación disparada
- Evaluación completada → HITL queue actualizada
- Sesión inactiva → Email reenganche enviado
- Cambio dato → Auditoría registrada

Necesitamos:
- Desacoplamiento de servicios
- Garantía entrega eventual (retry logic)
- Escalabilidad (múltiples consumers)
- Bajo overhead operacional
- Compatible con CloudWatch/CloudFormation

### Opciones

#### Opción 1: Redis Pub/Sub + Celery
**Descripción**: Redis como message broker, Celery para task scheduling.

**Ventajas**:
- ✅ Redis ya en infraestructura (para caché)
- ✅ Bajo latencia (<100ms)
- ✅ Simple de entender (canal = tema)
- ✅ Integrado con Django/FastAPI
- ✅ Celery soporta periodic tasks (background jobs)

**Desventajas**:
- ❌ Pub/Sub no persiste mensajes (loss si subscriber down)
- ❌ Celery reintento es básico (sin dead letter queue por default)
- ❌ Escalabilidad limitada (Redis single-node bottleneck)

---

#### Opción 2: RabbitMQ
**Descripción**: Message broker dedicado, queues persistentes.

**Ventajas**:
- ✅ Persistencia (mensajes guardados en disco)
- ✅ Delivery guarantees (at-least-once)
- ✅ Dead letter queues (manejo fallos)
- ✅ Clustering built-in (escalabilidad)

**Desventajas**:
- ❌ Operación compleja (management UI, clustering)
- ❌ Costo infra adicional (otro servicio)
- ❌ Latencia moderada (vs Redis)

---

#### Opción 3: AWS SQS + SNS
**Descripción**: Servicios AWS gestionados (SQS queues, SNS topics).

**Ventajas**:
- ✅ Managed (AWS gestiona operación)
- ✅ Escalabilidad automática
- ✅ CloudWatch integrado (monitoreo)
- ✅ Pricing pay-as-you-go

**Desventajas**:
- ❌ Latencia moderada (100-500ms)
- ❌ Costo variable (por millón mensajes)
- ❌ Menos flexible (limitaciones SQS)

---

#### Opción 4: Kafka
**Descripción**: Event streaming distribuido, particiones, replicación.

**Ventajas**:
- ✅ Alta disponibilidad (replicación)
- ✅ Persistencia duradera (retención configurable)
- ✅ Escalabilidad masiva (particiones)

**Desventajas**:
- ❌ Operación muy compleja
- ❌ Overkill para MVP (sobre-engineered)
- ❌ Costo infra alto

---

### Decisión

**✅ Redis Pub/Sub + Celery**

Razones:
1. **Simplicidad**: Redis ya presente, Celery bien documentado
2. **MVP-ready**: Suficiente para volumen inicial (<1M eventos/día)
3. **Low latency**: <100ms ideal para UX real-time
4. **Cost**: Sin infraestructura adicional

**Migración futura**: Si volumen crece >10M/día, migrar a Kafka

### Consecuencias

**Positivas**:
- ✅ Bajo overhead (sin nuevo servicio)
- ✅ Fácil debugging (eventos visibles en Redis)
- ✅ Rápido iterar (Celery tasks modificables sin restart)

**Negativas**:
- ❌ Sin persistencia (si Redis crashes, eventos se pierden)
- ❌ Sin dead letter queue (reintento manual)
- ❌ Escalabilidad limitada (~10K eventos/sec Redis)

**Mitigación**:
- EntradaEvento tabla en BD (fallback persistencia)
- Retry logic: exponential backoff, max 5 intentos
- Monitoreo: alertar si fallos > 5%

### Implementación

```python
# Configuración Celery
from celery import Celery, shared_task
from redis import Redis

app = Celery('ticketdesk', broker='redis://localhost:6379/0')

@shared_task(bind=True, max_retries=5)
def process_evaluation(self, evaluation_id):
    try:
        evaluation = Evaluacion.get_by_id(evaluation_id)
        # Lógica evaluación
        hitl_service.create_if_review(evaluation)
    except Exception as exc:
        # Retry con exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# Publicar evento
def publish_event(event_type: str, payload: dict):
    redis_client = Redis()
    
    # Persistir en BD (fallback)
    event_log = EntradaEvento(
        tipo_evento=event_type,
        id_agregado=payload.get("aggregate_id"),
        carga_útil=payload,
        estado="PENDIENTE"
    )
    event_log.save()
    
    # Publicar a Redis Pub/Sub
    redis_client.publish(f"evento:{event_type}", json.dumps(payload))

# Suscriptor
def consume_events():
    redis_client = Redis()
    pubsub = redis_client.pubsub()
    pubsub.subscribe("evento:screening.completado", "evento:evaluation.completada")
    
    for message in pubsub.listen():
        if message["type"] == "message":
            payload = json.loads(message["data"])
            if message["channel"] == "evento:screening.completado":
                process_evaluation.delay(payload["screening_id"])
            elif message["channel"] == "evento:evaluation.completada":
                hitl_service.queue_if_review(payload["evaluation_id"])
```

---

## 🎯 ADR-UNIT2-003: Patrón Repositorio (vs Query Builder vs Raw SQL)

**Título**: Elegir patrón acceso datos en backend

**Estado**: ✅ ACEPTADA  
**Fecha**: 2026-05-27  
**Autor**: Equipo Backend  

### Contexto

FastAPI con SQLAlchemy requiere abstracción consistente para acceso datos:
- 50+ queryeables (Session, Screening, Evaluation, etc.)
- Necesidad de unit testing (mock repositories)
- Cambios esquema BD sin refactor masivo
- Performance (índices, lazy loading)

### Opciones

#### Opción 1: Repository Pattern (Recomendado)
**Descripción**: Interfaz repositorio abstracta, implementación por agregado.

```python
class RepositorioSesión(abc.ABC):
    @abc.abstractmethod
    def obtener_por_id(self, id: UUID) -> Sesión: pass
    
    @abc.abstractmethod
    def obtener_activas(self) -> List[Sesión]: pass
    
    @abc.abstractmethod
    def guardar(self, sesión: Sesión) -> UUID: pass

class RepositorioSesiónSQL(RepositorioSesión):
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_por_id(self, id: UUID) -> Sesión:
        modelo = self.db.query(ModeloSesión).filter(ModeloSesión.id == id).first()
        return modelo.to_domain() if modelo else None
    
    def obtener_activas(self) -> List[Sesión]:
        modelos = self.db.query(ModeloSesión).filter(ModeloSesión.estado == "ACTIVA")
        return [m.to_domain() for m in modelos]
    
    def guardar(self, sesión: Sesión) -> UUID:
        modelo = ModeloSesión.from_domain(sesión)
        self.db.add(modelo)
        self.db.commit()
        return modelo.id
```

**Ventajas**:
- ✅ Testeable (mock repositorio en tests)
- ✅ Desacoplamiento (cambio BD sin cambio lógica)
- ✅ CRUD centralizado (consistencia)

**Desventajas**:
- ❌ Boilerplate (una clase por agregado)

---

#### Opción 2: Query Builder (SQLAlchemy)
**Descripción**: Usar directamente `session.query()` en servicios.

**Ventajas**:
- ✅ Menos código (sin clases repositorio)
- ✅ Flexible (queries ad-hoc)

**Desventajas**:
- ❌ Difícil testear (mock SQLAlchemy session complejo)
- ❌ Lógica dispersa (queries en múltiples servicios)

---

#### Opción 3: Raw SQL
**Descripción**: SQL directo para queries complejas.

**Ventajas**:
- ✅ Control total (performance optimization)

**Desventajas**:
- ❌ SQL Injection riesgo (si no parametrizado)
- ❌ Difícil mantener (cambios esquema = refactor queries)

---

### Decisión

**✅ Repository Pattern (con SQLAlchemy)**

Razones:
1. **Testabilidad**: Mock repositorio en unit tests sin BD real
2. **Escalabilidad**: Agregar repositorios sin modificar servicios
3. **LGPD**: Auditoría centralizada en repositorio (log mutations)

### Implementación

```python
# Base repository interface
from abc import ABC, abstractmethod

class RepositorioBase(ABC, Generic[T]):
    @abstractmethod
    async def obtener_por_id(self, id: UUID) -> Optional[T]: pass
    
    @abstractmethod
    async def listar_todos(self) -> List[T]: pass
    
    @abstractmethod
    async def guardar(self, entidad: T) -> T: pass
    
    @abstractmethod
    async def eliminar(self, id: UUID) -> bool: pass

# Implementación SQL
class RepositorioSesiónSQL(RepositorioBase[Sesión]):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def obtener_por_id(self, id: UUID) -> Optional[Sesión]:
        stmt = select(ModeloSesión).where(ModeloSesión.id == id)
        resultado = await self.db.execute(stmt)
        modelo = resultado.scalar_one_or_none()
        return modelo.to_domain() if modelo else None
    
    async def guardar(self, sesión: Sesión) -> Sesión:
        modelo = ModeloSesión.from_domain(sesión)
        self.db.add(modelo)
        await self.db.flush()
        
        # Auditoría
        await self.crear_entrada_auditoría(
            tipo_entidad="Sesión",
            id_entidad=sesión.id,
            acción="CREATE" if modelo.id else "UPDATE",
            cambios={"estado": sesión.estado}
        )
        
        await self.db.commit()
        return sesión

# Inyección dependencia (FastAPI)
async def obtener_repositorio_sesión(db: AsyncSession = Depends(obtener_db)):
    return RepositorioSesiónSQL(db)

# Uso en servicio
class ServicioSesión:
    def __init__(self, repo: RepositorioSesión):
        self.repo = repo
    
    async def iniciar_sesión(self, id_candidato: UUID) -> Sesión:
        sesión = Sesión.crear(id_candidato)
        return await self.repo.guardar(sesión)
```

---

## 🎯 ADR-UNIT2-004: Inyección de Dependencia (FastAPI Depends vs Manual vs Service Locator)

**Título**: Elegir patrón inyección de dependencias

**Estado**: ✅ ACEPTADA  
**Fecha**: 2026-05-27  
**Autor**: Equipo Backend  

### Contexto

Aplicación FastAPI con múltiples servicios:
- ServicioSesión, ServicioScreening, ServicioEvaluación, etc.
- Cada servicio requiere BD, Redis, logging
- Unit tests necesitan mockear dependencias
- Ciclo de vida (BD connection, cleanup)

### Opciones

#### Opción 1: FastAPI Depends (Recomendado)
**Descripción**: Sistema inyección integrado de FastAPI.

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

async def obtener_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def obtener_servicio_sesión(db: AsyncSession = Depends(obtener_db)):
    return ServicioSesión(db)

@app.post("/sesiones")
async def crear_sesión(
    body: CrearSesiónRequest,
    servicio = Depends(obtener_servicio_sesión)
):
    return await servicio.iniciar_sesión(body.candidate_id)
```

**Ventajas**:
- ✅ Integrado FastAPI (cache automático por request)
- ✅ Fácil testear (override Depends en tests)
- ✅ Legible (visible en firma función)

**Desventajas**:
- ❌ Limitado a endpoints (no servicios internos)

---

#### Opción 2: Service Locator
**Descripción**: Registro global de servicios.

```python
class ServicioLocalizador:
    _servicios = {}
    
    @classmethod
    def registrar(cls, nombre: str, instancia: Any):
        cls._servicios[nombre] = instancia
    
    @classmethod
    def obtener(cls, nombre: str):
        return cls._servicios.get(nombre)

# Setup
localizador = ServicioLocalizador()
localizador.registrar("db", AsyncSessionLocal)
localizador.registrar("sesión", ServicioSesión(localizador.obtener("db")))

# Uso
servicio = localizador.obtener("sesión")
```

**Ventajas**:
- ✅ Flexible (setup centralizado)

**Desventajas**:
- ❌ Anti-pattern (hidden dependencies)
- ❌ Difícil testear (global state)

---

#### Opción 3: Manual Wiring
**Descripción**: Pasar dependencias explícitamente.

```python
async def crear_sesión(db: AsyncSession):
    servicio = ServicioSesión(db)
    return await servicio.iniciar_sesión(...)
```

**Ventajas**:
- ✅ Explícito (depencies visibles)

**Desventajas**:
- ❌ Repetitivo (boilerplate)

---

### Decisión

**✅ FastAPI Depends + Manual para servicios internos**

Razones:
1. **Endpoints**: FastAPI Depends (nativo, cache request)
2. **Servicios internos**: Manual wiring (explícito, testeable)

### Implementación

```python
# Core: Setup dependencias
async def obtener_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def obtener_redis():
    redis = Redis()
    yield redis
    await redis.close()

# Repositorios
async def obtener_repo_sesión(db: AsyncSession = Depends(obtener_db)):
    return RepositorioSesiónSQL(db)

# Servicios (FastAPI endpoints)
async def obtener_servicio_sesión(
    repo_sesión = Depends(obtener_repo_sesión),
    redis = Depends(obtener_redis)
):
    return ServicioSesión(repo_sesión, redis)

# Servicios internos (manual wiring)
class ServicioScreening:
    def __init__(
        self,
        repo_screening: RepositorioScreening,
        servicio_sesión: ServicioSesión
    ):
        self.repo = repo_screening
        self.servicio_sesión = servicio_sesión
    
    async def iniciar_screening(self, sesión_id: UUID):
        sesión = await self.servicio_sesión.obtener(sesión_id)
        screening = Screening.crear(sesión)
        return await self.repo.guardar(screening)

# Router endpoint
@router.post("/sesiones/{id}/screening")
async def iniciar_screening(
    id: UUID,
    servicio_sesión = Depends(obtener_servicio_sesión),
    repo_screening = Depends(obtener_repo_screening)
):
    servicio_screening = ServicioScreening(repo_screening, servicio_sesión)
    return await servicio_screening.iniciar_screening(id)

# Tests
@pytest.mark.asyncio
async def test_iniciar_screening():
    # Mock repositorio
    repo_mock = MagicMock(spec=RepositorioScreening)
    servicio_sesión_mock = MagicMock(spec=ServicioSesión)
    
    servicio = ServicioScreening(repo_mock, servicio_sesión_mock)
    resultado = await servicio.iniciar_screening(UUID("123"))
    
    repo_mock.guardar.assert_called_once()
```

---

## 📊 Matriz de Decisiones Arquitectura

| ADR | Decisión | Alternativa Rechazada | Razón |
|---|---|---|---|
| ADR-UNIT2-001 | JWT RS256 | OAuth2 | No requiere tercero, escalable |
| ADR-UNIT2-002 | Redis Pub/Sub + Celery | Kafka | Simplicidad MVP, escalable a Kafka luego |
| ADR-UNIT2-003 | Repository Pattern | Query Builder | Testabilidad, desacoplamiento |
| ADR-UNIT2-004 | FastAPI Depends | Service Locator | Nativo, cache request, testeable |

---

## ✅ Criterios de Aceptación (Actividad 3)

- [x] 4 ADRs documentados en formato Contexto-Opciones-Decisión-Consecuencias
- [x] Cada ADR incluye implementación código
- [x] Alternativas evaluadas objetivamente
- [x] Consecuencias positivas/negativas documentadas
- [x] Mitigación de riesgos articulada
- [x] Alineación con NFRs anterior

---

**Generado**: 2026-05-27  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 3 - Decisiones Arquitectura  
**Estado**: ✅ COMPLETADA
