# Unit 6: Cumplimiento (LGPD/Compliance) — Actividad 2: Requisitos No-Funcionales

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 2 - Requisitos No-Funcionales (NFR)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**6 Requisitos No-Funcionales** para compliance con SLAs legales y auditables.

---

## 🎯 NFR 1: Auditoría Completa (100% Trail)

**Categoría**: Trazabilidad, Integridad

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Cobertura auditoría | 100% eventos | 100% |
| Integridad registros | 0 gaps | 0 |
| Latencia logging | <100ms (no bloquea) | <500ms |
| Búsqueda audit logs | <2s (CloudWatch Insights) | <10s |
| Retención | 7 años | 7 años (legal) |

### Criterios de Aceptación

- [ ] Cada CREATE/UPDATE/DELETE auditada (usuario, timestamp, IP, user_agent, cambios)
- [ ] Ningún evento perdido (durabilidad)
- [ ] Logs accesibles <2s (búsqueda rápida)
- [ ] 0 falsos negativos (ningún evento omitido)

### Estrategia Medición

```python
# Validar cobertura auditoría
def test_audit_coverage():
    # Para cada objeto en BD, debe existir entrada auditoría CREATE
    usuarios = db.query(Usuario).limit(100)
    
    for user in usuarios:
        audit_entry = db.query(EntradaAuditoría).filter(
            EntradaAuditoría.tipo_evento == "CREATE",
            EntradaAuditoría.entidad_id == user.id,
            EntradaAuditoría.entidad_tipo == "Usuario"
        ).first()
        
        assert audit_entry is not None, f"Usuario {user.id} sin CREATE audit"
        assert audit_entry.usuario_id is not None
        assert audit_entry.timestamp is not None
        assert audit_entry.dirección_ip is not None

# CloudWatch Insights búsqueda rápida
# Consulta: fields @timestamp, @message | filter usuario_id = "xyz" | stats count()
# Tiempo: <2 segundos
```

---

## 🎯 NFR 2: Derecho Olvido SLA (<24 horas)

**Categoría**: Privacidad, Legal

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Hard delete SLA | <24 horas | <48 horas |
| Completitud eliminación | 100% (0 residuos) | 100% |
| Notificación usuario | <1h post-completada | <2h |
| Reversibilidad | <1 hora antes completar | <2 horas |

### Criterios de Aceptación

- [ ] Hard delete iniciado <1h post-aprobación
- [ ] Todos datos eliminados (sesiones, screenings, evaluaciones, consentimientos, logs)
- [ ] 0 registros residuales en BD/S3/Elasticsearch
- [ ] Usuario notificado < 1 hora post-completada
- [ ] Reversible hasta hard_delete_iniciado (cancellable)

### Estrategia Medición

```python
# Celery task para hard delete
@app.task(time_limit=3600)  # Max 1 hour
def hard_delete_user_data(solicitud_eliminación_id: UUID):
    """Hard delete con SLA <24h"""
    solicitud = db.query(SolicitudEliminación).get(solicitud_eliminación_id)
    
    start = time.time()
    
    try:
        # 1. Marcar para eliminación (reversible)
        solicitud.hard_delete_iniciado_en = datetime.utcnow()
        db.commit()
        
        # 2. Eliminar sesiones
        db.query(Sesión).filter(Sesión.id_usuario == solicitud.id_usuario).delete()
        
        # 3. Eliminar screenings
        db.query(Screening).filter(Screening.id_usuario == solicitud.id_usuario).delete()
        
        # 4. Eliminar evaluaciones
        db.query(Evaluación).filter(Evaluación.id_usuario == solicitud.id_usuario).delete()
        
        # 5. Eliminar consentimientos
        db.query(Consentimiento).filter(Consentimiento.id_usuario == solicitud.id_usuario).delete()
        
        # 6. Eliminar de S3 (transcripciones)
        s3_keys = s3.list_objects_v2(
            Bucket='transcripciones',
            Prefix=f'{solicitud.id_usuario}/'
        )
        for obj in s3_keys.get('Contents', []):
            s3.delete_object(Bucket='transcripciones', Key=obj['Key'])
        
        # 7. Eliminar de Elasticsearch (índices búsqueda)
        es.delete_by_query(
            index='screenings',
            body={'query': {'term': {'id_usuario': solicitud.id_usuario}}}
        )
        
        db.commit()
        
        # 8. Notificar usuario
        send_email(
            to=solicitud.usuario.email,
            subject="Datos eliminados - Derecho olvido",
            body="Tus datos han sido eliminados según solicitud"
        )
        
        solicitud.hard_delete_completado_en = datetime.utcnow()
        solicitud.estado = EstadoSolicitud.COMPLETADA
        db.commit()
        
        # 9. Registrar en auditoría
        log_audit_entry(
            tipo_evento="HARD_DELETE",
            entidad_id=solicitud.id_usuario,
            cambios={"deleted_records": solicitud.registros_eliminados}
        )
        
    except Exception as e:
        # Si falla, reversible hasta ahora
        solicitud.hard_delete_iniciado_en = None
        db.rollback()
        raise

# Verificar SLA
def test_hard_delete_sla():
    solicitud = SolicitudEliminación(estado=EstadoSolicitud.APROBADA)
    db.add(solicitud)
    db.commit()
    
    # Trigger task
    task = hard_delete_user_data.apply_async(
        args=[solicitud.id],
        countdown=5  # Ejecutar en 5 segundos
    )
    
    # Esperar completación
    start = time.time()
    result = task.get(timeout=3600)  # Max 1 hora
    elapsed = time.time() - start
    
    assert elapsed < 86400, f"Hard delete took {elapsed}s > 24h SLA"
```

---

## 🎯 NFR 3: Integridad Consentimiento

**Categoría**: Privacidad, Validación

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Consentimiento documentado | 100% screening | 100% |
| Verificación integridad | SHA256 hash | SHA256 hash |
| Revocación auditable | 100% logged | 100% |
| Revalidación annual | Auto-recordatorio | <90 días vencimiento |

### Criterios de Aceptación

- [ ] Ningún screening sin consentimiento documentado
- [ ] Hash consentimiento verificado (documento no modificado)
- [ ] Cada revocación auditada (usuario, razón, timestamp)
- [ ] Email recordatorio 30 días antes vencimiento

### Estrategia Medición

```python
# Validación consentimiento antes screening
@app.post("/api/screenings")
async def create_screening(screening_data: ScreeningSchema):
    usuario = db.query(Usuario).get(screening_data.usuario_id)
    
    # Validar consentimiento activo
    consentimiento = db.query(Consentimiento).filter(
        Consentimiento.id_usuario == usuario.id,
        Consentimiento.estado == "ACTIVO",
        Consentimiento.válido_hasta > datetime.utcnow()
    ).first()
    
    if not consentimiento:
        raise HTTPException(status_code=403, detail="Consentimiento requerido")
    
    # Verificar integridad documento
    import hashlib
    documento_hash_actual = hashlib.sha256(
        consentimiento.copia_local_texto.encode()
    ).hexdigest()
    
    if documento_hash_actual != consentimiento.integridad_hash:
        raise HTTPException(status_code=400, detail="Documento modificado")
    
    # Crear screening
    screening = Screening(
        usuario_id=usuario.id,
        consentimiento_id=consentimiento.id
    )
    db.add(screening)
```

---

## 🎯 NFR 4: Reportes Compliance Monthly

**Categoría**: Gobernanza, Reporte

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Generación reporte | 100% mensual | 100% |
| Completitud métricas | 0 datos faltantes | 0 |
| Latencia generación | <1h | <2h |
| Aprobación DPO | <3 días | <5 días |

### Criterios de Aceptación

- [ ] Reporte LGPD generada primer día mes para mes anterior
- [ ] Todas métricas completadas (0 NULLs)
- [ ] Generada <1h automáticamente
- [ ] DPO aprobación <3 días
- [ ] Reporte archivada 10 años

### Estrategia Medición

```python
# Scheduled task (Celery Beat)
# En settings: CELERY_BEAT_SCHEDULE = {
#     'generate-compliance-report': {
#         'task': 'app.modules.compliance.tasks.generate_compliance_report',
#         'schedule': crontab(hour=0, minute=0, day_of_month=1),  # 1er día mes
#     }
# }

@app.task
def generate_compliance_report(año: int, mes: int):
    """Generar reporte LGPD monthly"""
    
    período = f"{año}-{mes:02d}"
    
    # Agregar métricas
    métricas = {
        "total_usuarios": db.query(Usuario).count(),
        "total_consentimientos": db.query(Consentimiento).filter(
            extract('year', Consentimiento.otorgado_en) == año,
            extract('month', Consentimiento.otorgado_en) == mes
        ).count(),
        "consentimientos_revocados": db.query(Consentimiento).filter(
            Consentimiento.estado == "REVOCADO",
            extract('year', Consentimiento.revocado_en) == año,
            extract('month', Consentimiento.revocado_en) == mes
        ).count(),
        "solicitudes_derecho_olvido": db.query(SolicitudEliminación).filter(
            extract('year', SolicitudEliminación.solicitada_en) == año,
            extract('month', SolicitudEliminación.solicitada_en) == mes
        ).count(),
        # ... más métricas
    }
    
    reporte = ReporteCompliance(
        período=período,
        año_mes=f"{año}-{mes:02d}",
        generada_en=datetime.utcnow(),
        métricas_lgpd=métricas,
        estado="BORRADOR"  # Esperar aprobación DPO
    )
    db.add(reporte)
    db.commit()
    
    # Notificar DPO
    send_email(
        to=settings.DPO_EMAIL,
        subject=f"Reporte LGPD {período} lista para aprobación",
        body=f"Reporte compliance del mes {período} lista para revisar"
    )
```

---

## 🎯 NFR 5: Encriptación (AES-256 + KMS)

**Categoría**: Seguridad, Protección datos

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Datos en tránsito | TLS 1.3 | TLS 1.2 |
| Datos en reposo | AES-256 KMS | AES-256 |
| Rotación claves | Yearly | Yearly |
| Acceso KMS auditado | 100% logged | 100% |

### Criterios de Aceptación

- [ ] HTTPS/TLS 1.3 obligatorio
- [ ] Consentimientos encriptados S3 (KMS)
- [ ] PII en BD encriptado
- [ ] Rotación claves anual con auditoría

---

## 🎯 NFR 6: Observabilidad Compliance

**Categoría**: Monitoreo, Alertas

### Requisitos Cuantificados

| Métrica | Objetivo | Herramienta |
|---------|----------|----------|
| Alertas violations | <1min | CloudWatch Alarms |
| Dashboard compliance | Real-time | Grafana |
| Log retention | 7 años | CloudWatch |
| Audit trail search | <2s | CloudWatch Insights |

---

## ✅ Criterios de Aceptación (Actividad 2)

- [x] 6 NFRs documentados con SLAs legales
- [x] Métricas cuantificadas y críticas
- [x] Estrategias medición con código
- [x] Integración compliance checks

---

**Generado**: 2026-05-27  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 2 - Requisitos No-Funcionales  
**Estado**: ✅ COMPLETADA
