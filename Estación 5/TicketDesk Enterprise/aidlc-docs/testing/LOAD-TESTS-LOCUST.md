# Load Tests — Locust Suite

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Testing  
**Framework**: Locust (Python)  
**Target**: 200 concurrent screenings + 50 concurrent evaluations  
**Fecha**: 2026-05-27  

---

## 📊 Objetivos de Carga

| Escenario | Usuarios | RPS | P95 Target | P99 Target | Error Rate |
|---|---|---|---|---|---|
| **Screenings** | 200 | 50 | <3s | <5s | <0.5% |
| **Evaluations** | 50 | 25 | <500ms | <1s | <0.5% |
| **Mixed Load** | 250 | 75 | <2s | <4s | <0.5% |

---

## 🏗️ Estructura de Tests

```
locustfiles/
├── screenings_load.py          # 200 candidatos simultáneos
├── evaluations_load.py         # 50 reclutadores simultáneos
├── mixed_load.py               # 250 usuarios combinados
│
└── utils/
    ├── auth_helper.py          # Generación de tokens JWT
    ├── sse_handler.py          # Manejo de SSE (Server-Sent Events)
    └── metrics_collector.py     # Colección de métricas personalizadas
```

---

## 📝 Escenario 1: Screenings Concurrentes (200 usuarios)

### screenings_load.py

```python
"""
Locust load test para 200 candidatos simultáneos haciendo screening.
Simula: crear sesión → enviar respuestas → completar screening.
Métrica crítica: SSE latencia <100ms, respuesta bot <3s P95.
"""

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import random
import json
import time
from uuid import uuid4
from auth_helper import generate_jwt_token
from metrics_collector import CustomMetrics

class CandidateScreeningUser(FastHttpUser):
    """Simula un candidato haciendo screening."""
    
    wait_time = between(2, 5)  # 2-5 segundos entre acciones
    
    def on_start(self):
        """Se ejecuta al iniciar usuario (login)."""
        self.session_id = None
        self.candidate_id = str(uuid4())
        self.campaign_id = "campaign-prod-001"
        self.token = generate_jwt_token(
            sub=self.candidate_id,
            tipo="candidato",
            exp=3600
        )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(1)
    def create_session(self):
        """Crear sesión de screening (CREADA)."""
        payload = {
            "id_candidato": self.candidate_id,
            "id_campaña": self.campaign_id,
            "metadatos": {
                "dispositivo": random.choice(["mobile", "tablet", "desktop"]),
                "navegador": random.choice(["Chrome", "Safari", "Firefox"]),
                "so": random.choice(["iOS", "Android", "Windows", "macOS"]),
                "ip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "ubicación": None
            }
        }
        
        with self.client.post(
            "/sessions",
            json=payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.session_id = data.get("id_sesión")
                response.success()
            else:
                response.failure(f"Failed to create session: {response.status_code}")
    
    @task(3)
    def start_and_chat(self):
        """Iniciar sesión → enviar mensaje → recibir respuesta SSE."""
        if not self.session_id:
            return
        
        # Paso 1: Iniciar sesión (CREADA → ACTIVA)
        init_response = self.client.post(
            f"/sessions/{self.session_id}/iniciar",
            headers=self.headers,
            catch_response=True
        )
        
        if init_response.status_code != 200:
            init_response.failure(f"Failed to start session: {init_response.status_code}")
            return
        
        # Paso 2: Enviar mensaje (con SSE streaming)
        message = random.choice([
            "Tengo 5 años de experiencia en Python",
            "Mi mayor logro fue liderar un proyecto de migración a microservicios",
            "Prefiero trabajar en equipos ágiles con retrospectivas semanales",
            "Mi stack tecnológico favorito es FastAPI + React + PostgreSQL"
        ])
        
        payload = {"contenido": message}
        
        # Medir latencia de SSE
        start_time = time.time()
        
        with self.client.post(
            f"/sessions/{self.session_id}/mensajes",
            json=payload,
            headers=self.headers,
            stream=True,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Contar tokens del stream SSE
                token_count = 0
                first_token_time = None
                
                for line in response.iter_lines():
                    if line.startswith(b"data: "):
                        if first_token_time is None:
                            first_token_time = time.time() - start_time
                        token_count += 1
                
                sse_latency = first_token_time or (time.time() - start_time)
                total_latency = time.time() - start_time
                
                # Registrar métricas
                CustomMetrics.record_sse_latency(sse_latency, self.candidate_id)
                CustomMetrics.record_tokens_streamed(token_count, self.candidate_id)
                
                response.success()
            else:
                response.failure(f"Failed to send message: {response.status_code}")
    
    @task(1)
    def complete_session(self):
        """Completar sesión (ACTIVA → COMPLETADA)."""
        if not self.session_id:
            return
        
        with self.client.post(
            f"/sessions/{self.session_id}/completar",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                assert data.get("estado") == "COMPLETADA"
                self.session_id = None  # Reset para siguiente iteración
                response.success()
            else:
                response.failure(f"Failed to complete session: {response.status_code}")


class ScreeningsLoadTest(CandidateScreeningUser):
    """Especialización: solo screenings."""
    tasks = {
        create_session: 1,
        start_and_chat: 5,
        complete_session: 2,
    }
```

---

## 📝 Escenario 2: Evaluaciones Concurrentes (50 reclutadores)

### evaluations_load.py

```python
"""
Locust load test para 50 reclutadores simultáneos evaluando candidatos.
Simula: obtener cola → revisar transcripción → completar evaluación.
Métrica crítica: evaluación POST <500ms P95, sin errores RBAC.
"""

from locust import HttpUser, task, between
from locust.contrib.fasthttp import FastHttpUser
import random
import json
import time
from uuid import uuid4
from auth_helper import generate_jwt_token
from metrics_collector import CustomMetrics

class RecruiterEvaluationUser(FastHttpUser):
    """Simula un reclutador evaluando candidatos."""
    
    wait_time = between(3, 8)  # 3-8 segundos entre evaluaciones
    
    def on_start(self):
        """Se ejecuta al iniciar usuario (login reclutador)."""
        self.recruiter_id = str(uuid4())
        self.campaign_id = "campaign-prod-001"
        self.token = generate_jwt_token(
            sub=self.recruiter_id,
            tipo="reclutador",
            role="RECRUITER",
            exp=3600
        )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.evaluation_queue = []
    
    @task(2)
    def fetch_evaluation_queue(self):
        """Obtener lista de candidatos para evaluar."""
        with self.client.get(
            f"/recruiter/queue?campaign_id={self.campaign_id}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.evaluation_queue = data.get("candidates", [])[:5]  # Próximos 5
                response.success()
            else:
                response.failure(f"Failed to fetch queue: {response.status_code}")
    
    @task(1)
    def get_evaluation_modal_data(self):
        """Obtener datos para abrir modal (rúbrica, transcripción)."""
        if not self.evaluation_queue:
            return
        
        candidate = self.evaluation_queue[0]
        candidate_id = candidate.get("id")
        session_id = candidate.get("session_id")
        
        # Fetch rúbrica
        with self.client.get(
            f"/campaigns/{self.campaign_id}/rubrica",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to fetch rubric: {response.status_code}")
        
        # Fetch transcripción
        with self.client.get(
            f"/sessions/{session_id}/transcript",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to fetch transcript: {response.status_code}")
    
    @task(5)
    def submit_evaluation(self):
        """Completar y enviar evaluación."""
        if not self.evaluation_queue:
            return
        
        candidate = self.evaluation_queue.pop(0)
        candidate_id = candidate.get("id")
        session_id = candidate.get("session_id")
        
        # Simular puntuaciones de rúbrica
        evaluation_payload = {
            "id_candidato": candidate_id,
            "id_sesión": session_id,
            "id_campaña": self.campaign_id,
            "criterios": [
                {
                    "id": "c-comunicacion",
                    "nombre": "Comunicación",
                    "score": random.randint(1, 5),
                    "peso": 30
                },
                {
                    "id": "c-tecnico",
                    "nombre": "Experiencia Técnica",
                    "score": random.randint(1, 5),
                    "peso": 40
                },
                {
                    "id": "c-cultural",
                    "nombre": "Fit Cultural",
                    "score": random.randint(1, 5),
                    "peso": 30
                }
            ],
            "comentarios": f"Evaluación realizada por {self.recruiter_id}",
            "decisión": random.choice(["HIRE", "REJECT", "MAYBE"])
        }
        
        start_time = time.time()
        
        with self.client.post(
            f"/evaluations",
            json=evaluation_payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            latency = time.time() - start_time
            
            if response.status_code == 201:
                CustomMetrics.record_evaluation_latency(latency, self.recruiter_id)
                response.success()
            else:
                response.failure(f"Failed to submit evaluation: {response.status_code}")


class EvaluationsLoadTest(RecruiterEvaluationUser):
    """Especialización: solo evaluaciones."""
    tasks = {
        fetch_evaluation_queue: 2,
        get_evaluation_modal_data: 1,
        submit_evaluation: 5,
    }
```

---

## 📝 Escenario 3: Mixed Load (250 usuarios)

### mixed_load.py

```python
"""
Locust load test combinado: 200 candidatos + 50 reclutadores simultáneos.
Prueba resiliencia del sistema bajo carga mixta realista.
"""

from locust import LoadTestShape
from screenings_load import ScreeningsLoadTest
from evaluations_load import EvaluationsLoadTest

class MixedLoadTest(LoadTestShape):
    """
    Rampa de carga: 0 → 250 usuarios en 5 minutos.
    250 usuarios constante durante 10 minutos.
    Rampa bajada: 250 → 0 en 5 minutos.
    Total: 20 minutos.
    """
    
    def tick(self):
        run_time = self.get_run_time()
        
        # Fase 1: Ramp up (0 → 250 usuarios en 300s)
        if run_time < 300:
            user_count = int((run_time / 300) * 250)
            return (user_count, 1)  # 1 spawn rate (1 usuario/s)
        
        # Fase 2: Plateau (250 usuarios constantes durante 10 min)
        elif run_time < 900:
            return (250, 1)
        
        # Fase 3: Ramp down (250 → 0 en 300s)
        elif run_time < 1200:
            user_count = int(250 * (1 - ((run_time - 900) / 300)))
            return (user_count, 1)
        
        # Fin
        else:
            return None


class ScreeningWorker(ScreeningsLoadTest):
    """Worker: 80% de carga (200 candidatos)."""
    weight = 4

class RecruiterWorker(EvaluationsLoadTest):
    """Worker: 20% de carga (50 reclutadores)."""
    weight = 1
```

---

## 🧪 Utilities: auth_helper.py

```python
"""
Helper para generar JWT tokens válidos durante los tests.
"""

import jwt
import json
from datetime import datetime, timedelta
from uuid import uuid4

class AuthHelper:
    """Genera tokens JWT para simulación de usuarios."""
    
    PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
[clave privada RSA-4096 para testing...]
-----END RSA PRIVATE KEY-----"""
    
    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
[clave pública RSA-4096 para testing...]
-----END PUBLIC KEY-----"""
    
    @staticmethod
    def generate_jwt_token(sub: str, tipo: str, exp: int = 3600, **kwargs) -> str:
        """
        Genera JWT token RS256 válido para testing.
        
        Args:
            sub: subject (candidate_id o recruiter_id)
            tipo: "candidato" | "reclutador"
            exp: tiempo de expiración en segundos
            **kwargs: claims adicionales (role, campaign_id, etc.)
        
        Returns:
            JWT token RS256 válido
        """
        now = datetime.utcnow()
        payload = {
            "sub": sub,
            "tipo": tipo,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=exp)).timestamp()),
            "jti": str(uuid4()),
        }
        payload.update(kwargs)
        
        token = jwt.encode(
            payload,
            AuthHelper.PRIVATE_KEY,
            algorithm="RS256"
        )
        
        return token
    
    @staticmethod
    def validate_token(token: str) -> bool:
        """Valida JWT token usando clave pública."""
        try:
            jwt.decode(
                token,
                AuthHelper.PUBLIC_KEY,
                algorithms=["RS256"]
            )
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

def generate_jwt_token(sub: str, tipo: str, exp: int = 3600, **kwargs) -> str:
    """Función simplificada para importar directamente."""
    return AuthHelper.generate_jwt_token(sub, tipo, exp, **kwargs)
```

---

## 📊 Utilities: metrics_collector.py

```python
"""
Colección de métricas personalizadas para Locust.
Registra: SSE latencia, tokens, evaluación latencia, etc.
"""

from locust import events
import json
from datetime import datetime

class CustomMetrics:
    """Recopila métricas customizadas durante load test."""
    
    sse_latencies = []
    evaluation_latencies = []
    tokens_per_session = []
    
    @staticmethod
    def record_sse_latency(latency_ms: float, user_id: str):
        """Registra latencia de primer token SSE."""
        CustomMetrics.sse_latencies.append({
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
            "user_id": user_id
        })
    
    @staticmethod
    def record_evaluation_latency(latency_ms: float, recruiter_id: str):
        """Registra latencia de POST /evaluations."""
        CustomMetrics.evaluation_latencies.append({
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
            "recruiter_id": recruiter_id
        })
    
    @staticmethod
    def record_tokens_streamed(count: int, user_id: str):
        """Registra cantidad de tokens streameados por SSE."""
        CustomMetrics.tokens_per_session.append({
            "timestamp": datetime.utcnow().isoformat(),
            "token_count": count,
            "user_id": user_id
        })
    
    @staticmethod
    def generate_report() -> dict:
        """Genera reporte de métricas personalizadas."""
        def percentile(data, p):
            idx = int(len(data) * p / 100)
            return sorted(data)[idx] if data else 0
        
        sse_values = [m["latency_ms"] for m in CustomMetrics.sse_latencies]
        eval_values = [m["latency_ms"] for m in CustomMetrics.evaluation_latencies]
        
        return {
            "sse_latency": {
                "count": len(sse_values),
                "p50": percentile(sse_values, 50),
                "p95": percentile(sse_values, 95),
                "p99": percentile(sse_values, 99),
            },
            "evaluation_latency": {
                "count": len(eval_values),
                "p50": percentile(eval_values, 50),
                "p95": percentile(eval_values, 95),
                "p99": percentile(eval_values, 99),
            }
        }

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta al final del test para generar reporte."""
    report = CustomMetrics.generate_report()
    print("\n" + "="*50)
    print("CUSTOM METRICS REPORT")
    print("="*50)
    print(json.dumps(report, indent=2))
```

---

## 🚀 Ejecución

### Instalar Locust

```bash
pip install locust
```

### Ejecutar Escenario 1: Screenings (200 usuarios)

```bash
locust -f screenings_load.py \
  --host https://api.ticketdesk.com \
  --users 200 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless
```

### Ejecutar Escenario 2: Evaluations (50 usuarios)

```bash
locust -f evaluations_load.py \
  --host https://api.ticketdesk.com \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m \
  --headless
```

### Ejecutar Escenario 3: Mixed Load (250 usuarios, 20 minutos)

```bash
locust -f mixed_load.py \
  --host https://api.ticketdesk.com \
  --headless \
  --run-time 20m
```

### Con Web UI (recomendado para análisis visual)

```bash
locust -f mixed_load.py \
  --host https://api.ticketdesk.com \
  --web
# Abre http://localhost:8089
```

---

## 📊 Métricas Esperadas

| Métrica | Target | Interpretación |
|---|---|---|
| **P95 Screenings** | <3s | 95% de las respuestas en <3s |
| **P99 Screenings** | <5s | 99% de las respuestas en <5s |
| **P95 Evaluations** | <500ms | Rápido para reclutador |
| **Error Rate** | <0.5% | Máximo 0.5% de fallos |
| **SSE Latency** | <100ms | Primer token en <100ms |

---

## ⚠️ Criterios de Fallo

Detener test si:
- ❌ Error rate > 1% (más de 1% de requests fallan)
- ❌ P95 latencia > 5s (50% de users espera >5s)
- ❌ API retorna 500+ en >100 requests
- ❌ Database CPU > 90% (índices no optimizados)

---

**Generado**: 2026-05-27  
**Fase**: Testing Phase  
**Estado**: 🟨 Batch 1 Listos
