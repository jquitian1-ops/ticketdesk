# Unit 4: Evaluación (Scoring Engine) — Actividad 4: Infraestructura

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 4 - Infraestructura: Componentes, Flujos, Despliegue  
**Fecha**: 2026-05-27  

---

## 🏗️ C4 Level 3: Scoring Pipeline

```
┌─ Scoring Engine Service ───────────────────────────────┐
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │    API POST /screenings/{id}/evaluation         │ │
│  │    Input: rubric_scores, feedback, decision     │ │
│  │    Output: evaluation_id, total_score           │ │
│  └──────────────────────────────────────────────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Scoring Service                              │ │
│  │  • Calcular scores criterio (regex rules)        │ │
│  │  • Aplicar pesos                                 │ │
│  │  • Determinar decisión (HIRE/REJECT)            │ │
│  │  • Extraer citas relevantes                      │ │
│  │  • Generar reporte                               │ │
│  └──────────────────────────────────────────────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Validación + Integridad                       │ │
│  │  • Verificar rúbrica versión                     │ │
│  │  • Validar scores en rango [0,10]               │ │
│  │  • Auditoría completa                            │ │
│  └──────────────────────────────────────────────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Guardar en BD + S3                            │ │
│  │  • Evaluación metadata en PostgreSQL              │ │
│  │  • Documento JSON en S3 (encriptado KMS)         │ │
│  │  • Publicar evento EvaluaciónCompletada          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
└──────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐       ┌──────────────┐      ┌──────────┐
   │PostgreSQL       │Redis Cache   │      │S3 Bucket │
   │(Evaluación,     │(Rúbrica,     │      │(Evaluat- │
   │Rúbrica)         │Criterios)    │      │iones)    │
   └─────────┘       └──────────────┘      └──────────┘
```

## 🗄️ Base de Datos (PostgreSQL)

```sql
CREATE TABLE Rúbrica (
    id UUID PRIMARY KEY,
    id_campaña UUID NOT NULL REFERENCES Campaña(id),
    nombre VARCHAR(255) NOT NULL,
    versión INT NOT NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVA',
    criterios JSONB NOT NULL,
    pesos_criterios JSONB NOT NULL,
    escala_puntuación JSONB NOT NULL,
    umbrales_aprobación JSONB NOT NULL,
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(id_campaña, versión)
);

CREATE TABLE Evaluación (
    id UUID PRIMARY KEY,
    id_screening UUID NOT NULL REFERENCES Screening(id),
    id_rúbrica UUID NOT NULL REFERENCES Rúbrica(id),
    id_evaluador UUID NOT NULL REFERENCES Usuario(id),
    estado VARCHAR(20) DEFAULT 'COMPLETADA',
    score_total FLOAT CHECK (score_total >= 0 AND score_total <= 10),
    decision VARCHAR(20) NOT NULL,
    feedback TEXT,
    tiempo_evaluación INT,
    scores_criterio JSONB NOT NULL,
    validación_manual BOOLEAN DEFAULT FALSE,
    evaluada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url_s3_documento VARCHAR(512),
    
    INDEX idx_screening ON Evaluación(id_screening),
    INDEX idx_estado ON Evaluación(estado),
    INDEX idx_decision ON Evaluación(decision)
);

CREATE TABLE ValidaciónRespuesta (
    id UUID PRIMARY KEY,
    id_screening UUID NOT NULL REFERENCES Screening(id),
    id_criterio UUID NOT NULL,
    tipo_validación VARCHAR(50) NOT NULL,
    resultado VARCHAR(20) NOT NULL,
    puntuación_validación FLOAT,
    detalles JSONB,
    validada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ☁️ Despliegue Terraform

```hcl
# Scoring service ECS
resource "aws_ecs_task_definition" "scoring_engine" {
  family      = "scoring-engine"
  cpu         = "1024"
  memory      = "2048"
  
  container_definitions = jsonencode([{
    name      = "scoring"
    image     = "scoring:latest"
    cpu       = 1024
    memory    = 2048
    
    environment = [
      { name = "DATABASE_URL", value = var.postgres_url },
      { name = "REDIS_URL", value = var.redis_url },
      { name = "S3_BUCKET", value = aws_s3_bucket.evaluations.id },
      { name = "KMS_KEY_ARN", value = aws_kms_key.main.arn }
    ]
    
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.scoring.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

# Auto-scaling para evaluaciones concurrentes
resource "aws_appautoscaling_policy" "scoring_scale" {
  policy_name = "scoring-scale-policy"
  
  metric_aggregation_type = "Average"
  target_tracking_scaling_policy_configuration {
    target_value = 75.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
```

## ✅ Criterios de Aceptación (Actividad 4)

- [x] C4 Level 3 pipeline documentada
- [x] Esquema BD con constraints
- [x] Terraform infrastructure
- [x] CloudWatch observabilidad

---

**Generado**: 2026-05-27  
**Unit**: 4 - Evaluación (Scoring Engine)  
**Actividad**: 4 - Infraestructura  
**Estado**: ✅ COMPLETADA
