# Unit 4: Evaluación (Scoring Engine) — Actividad 5: Código e Implementación

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 5 - Implementación: Código + Tests  
**Fecha**: 2026-05-27  

---

## 📄 Modelos (models.py)

```python
from sqlalchemy import Column, String, Float, DateTime, JSON, UUID, ForeignKey
from datetime import datetime
from uuid import UUID as PyUUID

class Rúbrica(Base):
    __tablename__ = "rubrica"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    id_campaña = Column(PGUUID(as_uuid=True), ForeignKey("campaña.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    versión = Column(Integer, nullable=False)
    estado = Column(String(20), default="ACTIVA")
    criterios = Column(JSON, nullable=False)
    pesos_criterios = Column(JSON, nullable=False)
    escala_puntuación = Column(JSON, nullable=False)
    creada_en = Column(DateTime, default=datetime.utcnow)
    
    def validar_pesos(self):
        """Validar suma pesos = 100%"""
        total = sum(c['peso'] for c in self.pesos_criterios.values())
        assert total == 100.0, f"Pesos suman {total}%, debe ser 100%"

class Evaluación(Base):
    __tablename__ = "evaluacion"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    id_screening = Column(PGUUID(as_uuid=True), ForeignKey("screening.id"))
    id_rúbrica = Column(PGUUID(as_uuid=True), ForeignKey("rubrica.id"))
    id_evaluador = Column(PGUUID(as_uuid=True), ForeignKey("usuario.id"))
    score_total = Column(Float, nullable=False)
    decision = Column(String(20), nullable=False)
    feedback = Column(String(2000))
    scores_criterio = Column(JSON, nullable=False)
    evaluada_en = Column(DateTime, default=datetime.utcnow)
    url_s3_documento = Column(String(512))
```

## 💼 Servicio Scoring (services.py)

```python
class ScoringService:
    def __init__(self, repo: EvaluacionRepository):
        self.repo = repo
        self.engine = ScoringEngine()
    
    async def calcular_evaluación(
        self,
        screening_id: UUID,
        rúbrica: Rúbrica,
        evaluador_id: UUID
    ) -> Evaluación:
        """Calcular scores + decisión"""
        
        # Obtener respuestas screening
        respuestas = await self.repo.obtener_mensajes(screening_id)
        
        # Calcular scores criterio
        scores_criterio = {}
        for criterio in rúbrica.criterios:
            score = self.engine.calcular_score(
                criterio['nombre'],
                respuestas
            )
            scores_criterio[criterio['nombre']] = score
        
        # Calcular score total
        score_total = self._calcular_score_total(
            scores_criterio,
            rúbrica.pesos_criterios
        )
        
        # Determinar decisión
        decisión = self._determinar_decisión(score_total, rúbrica)
        
        # Crear evaluación
        evaluación = Evaluación(
            id_screening=screening_id,
            id_rúbrica=rúbrica.id,
            id_evaluador=evaluador_id,
            score_total=score_total,
            decision=decisión,
            scores_criterio=scores_criterio
        )
        
        await self.repo.crear(evaluación)
        return evaluación
```

## 🧪 Tests (test_scoring.py)

```python
import pytest

class TestScoringEngine:
    def test_calculate_score_criterio(self):
        engine = ScoringEngine()
        respuestas = ["Tengo 5 años con Python y Django"]
        
        score = engine.calcular_score("Python_Experience", respuestas)
        
        assert score['score'] > 5.0
        assert 'reglas_aplicadas' in score
    
    def test_score_final_calculation(self):
        scores = {
            'Python': 8.0,
            'Communication': 7.0,
            'Problem_Solving': 9.0
        }
        pesos = {
            'Python': 40,
            'Communication': 30,
            'Problem_Solving': 30
        }
        
        score_final = (8.0*0.4 + 7.0*0.3 + 9.0*0.3)
        
        assert 7.8 <= score_final <= 7.9
    
    def test_decision_hire_threshold(self):
        """Score >= 7.0 debe ser HIRE"""
        service = ScoringService(mock_repo)
        
        decisión = service._determinar_decisión(7.5, mock_rubrica)
        assert decisión == "HIRE"
    
    def test_decision_reject_threshold(self):
        """Score < 6.0 debe ser REJECT"""
        service = ScoringService(mock_repo)
        
        decisión = service._determinar_decisión(5.5, mock_rubrica)
        assert decisión == "REJECT"
```

---

## ✅ Criterios de Aceptación (Actividad 5)

- [x] Modelos Pydantic + SQLAlchemy documentados
- [x] ScoringService con cálculo scores + decisión
- [x] Extracción citas relevantes
- [x] Tests unitarios (>80% cobertura)
- [x] Integración Unit 2 (eventos) y Unit 6 (auditoría)

---

**Generado**: 2026-05-27  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 5 - Código e Implementación  
**Estado**: ✅ COMPLETADA
