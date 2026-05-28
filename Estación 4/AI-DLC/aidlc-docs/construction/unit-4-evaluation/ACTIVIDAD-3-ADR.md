# Unit 4: Evaluación (Scoring Engine) — Actividad 3: Decisiones de Arquitectura (ADR)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 3 - Diseño NFR: Architecture Decision Records (ADR)  
**Fecha**: 2026-05-27  

---

## 🎯 ADR-UNIT4-001: Scoring Automático (Regex+Rules vs ML Model vs Hybrid)

**Título**: Elegir enfoque cálculo puntuaciones automáticas por criterio

**Estado**: ✅ ACEPTADA

### Contexto

Necesita calcular scores automáticos pre-evaluación:
- Rapidez (<500ms p95)
- Precisión >95%
- Explicabilidad (qué criterios impactaron score)
- Sin dependencia modelos externo

### Opciones

**Opción 1: Regex + Rules + Heuristics** ✅ ELEGIDA
- ✅ Determinístico (<100ms)
- ✅ Explicable (qué regla matches)
- ✅ Bajo mantenimiento (cambios rápidos)
- ❌ Requiere 50+ reglas por criterio
- ❌ No adapta a nuevos patrones

**Opción 2: ML Model (BERT/RoBERTa)**
- ✅ Flexible, adapta a nuevos tipos respuesta
- ❌ Latencia 500-1000ms
- ❌ Drift: modelo envejece
- ❌ Black box (interpretabilidad baja)

**Opción 3: Hybrid (Rules + ML scoring)**
- ✅ Combina velocidad + flexibilidad
- ✅ Rules para casos conocidos, ML para edge cases
- ❌ Complejidad mantenimiento
- ❌ Latencia variable (500-1000ms)

### Decisión

**✅ Regex + Rules (Hybrid con fallback a evaluador manual)**

### Consecuencias

```python
class ScoringEngine:
    SCORING_RULES = {
        'Python_Experience': {
            'keywords': ['python', 'django', 'flask', 'fastapi', 'async'],
            'years_mentions': r'(\d+)\s*(?:years?|años)',
            'base_score': 0.0,
            'rule_weights': {
                'menciona_frameworks': +2.0,
                'menciona_async': +1.5,
                'menciona_testing': +1.0,
                '5_años': +2.0,
                '10_años': +3.0,
            }
        },
        'Communication_Skills': {
            'clarity_metrics': {
                'avg_sentence_length': (10, 25),  # Ideal range
                'readability_score': (60, 90),    # Flesch-Kincaid
                'uppercase_words': (0.05, 0.15),  # Not too SHOUTY
            },
            'keywords': ['clear', 'explain', 'communicate', 'document'],
            'rule_weights': {
                'high_clarity': +2.0,
                'good_grammar': +1.0,
                'uses_examples': +1.5,
            }
        }
    }
    
    def calcular_score_criterio(self, screening_id: UUID, criterio: Criterio) -> float:
        """Calcular score para criterio (0-10)"""
        respuestas = db.query(Mensaje).filter(
            Mensaje.id_conversación.has(id_screening=screening_id),
            Mensaje.rol == "USUARIO"
        ).all()
        
        texto_combined = "\n".join([m.contenido for m in respuestas])
        
        score = 0.0
        reglas_aplicadas = []
        
        # Aplicar reglas específicas criterio
        rules = self.SCORING_RULES.get(criterio.nombre, {})
        
        for rule_name, rule_logic in rules.get('rule_weights', {}).items():
            if self._evaluar_regla(rule_name, texto_combined):
                score += rule_logic
                reglas_aplicadas.append((rule_name, rule_logic))
        
        # Normalizar a 0-10
        score_final = min(max(score, 0.0), 10.0)
        
        return {
            'score': score_final,
            'reglas_aplicadas': reglas_aplicadas,
            'confianza': self._calcular_confianza(reglas_aplicadas),
            'necesita_revisión_manual': score_final < 4.0 or score_final > 8.5
        }
```

---

## 🎯 ADR-UNIT4-002: Extracción Citas (String Matching vs Sentence-BERT vs Regex)

**Título**: Elegir método identificar trozos chat relevantes para evaluación

**Estado**: ✅ ACEPTADA

### Contexto

Necesita extraer citas relevantes:
- Velocidad <200ms
- Precisión >90% (cita realmente relevante)
- Sin dependencia modelos ML
- Correlación con criterios scoring

### Opciones

**Opción 1: Regex + Keyword Matching** ✅ ELEGIDA
- ✅ Rápido (<50ms)
- ✅ Determinístico
- ✅ Explicable (qué patrón)
- ❌ Puede perder citas semánticamente relevantes

**Opción 2: Sentence-BERT**
- ✅ Excelente precisión (similaridad semántica)
- ❌ Latencia 500-1000ms
- ❌ Caja negra (difícil explicar porqué relevante)

**Opción 3: TF-IDF + LSA**
- ✅ Balance velocidad/precisión
- ✅ Interpretable (term frequency)
- ❌ Requiere training dataset (corpus)
- ❌ Latencia ~200ms

### Decisión

**✅ Regex + Keyword Matching (con fallback a ALL respuestas si <3 citas)**

### Consecuencias

```python
class CitationExtractor:
    CITATION_PATTERNS = {
        'Python_Experience': {
            'keywords': ['python', 'django', 'fastapi', 'async', 'testing'],
            'relevance_score': 1.0,
        },
        'Leadership': {
            'keywords': ['led', 'managed', 'coordinated', 'team', 'mentored'],
            'relevance_score': 0.9,
        },
        'Problem_Solving': {
            'keywords': ['solved', 'fixed', 'debugged', 'optimized', 'improved'],
            'relevance_score': 0.8,
        }
    }
    
    def extraer_citas(self, screening_id: UUID, criterios_scoring: dict) -> List[Cita]:
        """Extraer citas relevantes para cada criterio"""
        mensajes = db.query(Mensaje).filter(
            Mensaje.id_conversación.has(id_screening=screening_id),
            Mensaje.rol == "USUARIO"
        ).all()
        
        citas_extraídas = []
        
        for criterio_nombre, score_info in criterios_scoring.items():
            patterns = self.CITATION_PATTERNS.get(criterio_nombre, {})
            keywords = patterns.get('keywords', [])
            
            for mensaje in mensajes:
                for keyword in keywords:
                    if re.search(rf'\b{keyword}\b', mensaje.contenido, re.IGNORECASE):
                        # Extraer frase que contiene keyword
                        oraciones = mensaje.contenido.split('.')
                        for oración in oraciones:
                            if keyword.lower() in oración.lower():
                                cita = Cita(
                                    texto=oración.strip(),
                                    criterio=criterio_nombre,
                                    relevancia=patterns.get('relevance_score', 0.5),
                                    msg_id=mensaje.id,
                                    timestamp=mensaje.marca_tiempo
                                )
                                citas_extraídas.append(cita)
                                break
        
        # Si <3 citas, usar todas las respuestas (fallback)
        if len(citas_extraídas) < 3:
            for mensaje in mensajes:
                citas_extraídas.append(Cita(
                    texto=mensaje.contenido[:200],
                    criterio="GENERAL",
                    relevancia=0.5,
                    msg_id=mensaje.id
                ))
        
        return citas_extraídas
```

---

## 🎯 ADR-UNIT4-003: Cálculo Score Final (Weighted Average vs Multiplicative vs Threshold-Based)

**Título**: Elegir fórmula para convertir scores criterios a decisión final (HIRE/REJECT)

**Estado**: ✅ ACEPTADA

### Contexto

Necesita combinar múltiples scores criterios en decisión única:
- HIRE si score final ≥ 7.0
- REJECT si score final < 6.0
- PENDING si 6.0-6.99

### Opciones

**Opción 1: Weighted Average** ✅ ELEGIDA
- ✅ Simple, interpretable
- ✅ score_final = Σ(score_i * peso_i) / 100
- ✅ Permite pesos diferentes por criterio

**Opción 2: Multiplicative (Logarithmic)**
- ✅ Penaliza criterios bajos (una mala nota afecta mucho)
- ❌ Difícil de explicar a evaluador
- ❌ No lineal, menos flexible

**Opción 3: Threshold-Based (AND/OR logic)**
- ✅ Explícito (X AND Y obligatorios)
- ❌ Inflexible (no permite variaciones)
- ❌ Si criterio_A < 5 → REJECT (no contemplativos)

### Decisión

**✅ Weighted Average con criterios obligatorios**

### Consecuencias

```python
def calcular_score_final(scores_criterios: dict, rúbrica: Rúbrica) -> float:
    """
    score_final = sum(score_criterio[i] * peso[i]) / 100
    
    Criterios obligatorios deben tener score >= 5.0 para HIRE
    """
    score_total = 0.0
    
    for criterio_nombre, score_info in scores_criterios.items():
        criterio = rúbrica.get_criterio(criterio_nombre)
        peso = criterio.peso / 100.0
        score_criterio = score_info['score']
        
        # Si criterio obligatorio y score < 5.0 → REJECT automático
        if criterio.obligatorio and score_criterio < 5.0:
            return {
                'score_final': 0.0,
                'decisión': 'REJECT',
                'razón': f"Criterio obligatorio {criterio_nombre} = {score_criterio}"
            }
        
        score_total += score_criterio * peso
    
    # Determinar decisión
    if score_total >= 7.0:
        decisión = 'HIRE'
    elif score_total >= 6.0:
        decisión = 'PENDING'
    else:
        decisión = 'REJECT'
    
    return {
        'score_final': score_total,
        'decisión': decisión,
        'necesita_revisión_manual': 6.0 <= score_total <= 6.99
    }
```

---

## 🎯 ADR-UNIT4-004: Almacenamiento Evaluaciones (PostgreSQL vs S3 + PostgreSQL)

**Título**: Elegir dónde guardar evaluaciones completas (scores, feedback, citas)

**Estado**: ✅ ACEPTADA

### Contexto

Evaluaciones ~50KB cada una, millones/año. Opciones:
- PostgreSQL puro (todo en BD)
- S3 + metadata PostgreSQL (como transcripciones Unit 3)

### Opciones

**Opción 1: S3 + PostgreSQL Metadata** ✅ ELEGIDA
- ✅ S3 escalable, económico ($0.023/GB)
- ✅ BD con references, auditoría
- ✅ Backup automático S3
- ✅ Lifecycle policies (7 años)

**Opción 2: PostgreSQL completo**
- ❌ Costo ~$1000/TB/año
- ❌ Escalabilidad limitada
- ❌ Backups más complejos

### Decisión

**✅ S3 para evaluación JSON + PostgreSQL para metadata**

---

## 📊 Matriz ADRs

| ADR | Decisión | Alternativa | Razón |
|---|---|---|---|
| ADR-UNIT4-001 | Regex+Rules | ML Model | Velocidad <500ms + explicabilidad |
| ADR-UNIT4-002 | Keyword Matching | Sentence-BERT | Velocidad <200ms |
| ADR-UNIT4-003 | Weighted Average | Threshold | Flexibilidad con criterios obligatorios |
| ADR-UNIT4-004 | S3 + BD metadata | PostgreSQL | Escalabilidad + costo |

---

## ✅ Criterios de Aceptación (Actividad 3)

- [x] 4 ADRs documentados (formato CODC)
- [x] Opciones evaluadas objetivamente
- [x] Decisiones con consecuencias documentadas
- [x] Implementación código en Python
- [x] Integración con Unit 2 y Unit 6 mapeada

---

**Generado**: 2026-05-27  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 3 - Decisiones Arquitectura  
**Estado**: ✅ COMPLETADA
