# Unit 2: Fundamentos Backend — Actividad 1: Reglas de Negocio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 1 - Diseño Funcional: Reglas de Negocio  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**10 Reglas de Negocio** que gobiernan operaciones de backend, con trazabilidad a agregados del dominio y criterios de aceptación.

---

## 🎯 Reglas de Negocio

### REGLA-BACKEND-01: Gestión del Ciclo de Vida de Sesión

**Descripción**: Las sesiones siguen una máquina de estados estricta con marcas de tiempo inmutables.

**Condición**: Usuario inicia screening o cambia de estado

**Acción**:
1. Sesión creada en estado CREADA (creada_en = ahora)
2. Usuario hace clic "Iniciar" → CREADA → ACTIVA (iniciada_en = ahora)
3. Usuario puede PAUSAR → temporizador de inactividad se reinicia en reanudación
4. Sesión se auto-completa después de (preguntas respondidas O timeout de 30 min)
5. Al completar → COMPLETADA (completada_en = ahora)
6. Al abandonar manualmente → ABANDONADA (abandonada_en = ahora, solo si ACTIVA >5min)

**Consecuencia**:
- Todas las marcas de tiempo inmutables (creación ≤ inicio ≤ finalización, sin reversiones)
- Registro de auditoría de transiciones de estado
- Permite informes de cumplimiento y analítica

**Origen**: functional-design.md § Ciclo de Vida de Sesión  
**Agregado Afectado**: AgregadoSesión

**Criterios de Aceptación**:
- [ ] Transiciones de estado validadas en pruebas
- [ ] Marcas de tiempo en orden cronológico
- [ ] Sesiones completadas/abandonadas son solo lectura

---

### REGLA-BACKEND-02: Consentimiento Previo al Procesamiento

**Descripción**: Ningún screening puede comenzar sin consentimiento explícito del candidato.

**Condición**: Candidato se une a sesión de screening

**Acción**:
1. Mostrar formulario de consentimiento (legal, procesamiento de datos, grabación)
2. Requerir acuerdo explícito con casilla de verificación para cada tipo
3. Capturar metadatos de consentimiento (dirección_ip, user_agent, fecha)
4. Solo después de TODOS los consentimientos dados → permitir progresión

**Consecuencia**:
- Incumplimiento es imposible (el formulario bloquea progresión)
- Registro de auditoría de consentimientos con metadatos
- Conforme a LGPD (documentado, revocable)

**Origen**: LGPD Artículo 8 (Requisito de Consentimiento)  
**Agregado Afectado**: AgregadoConsentimiento, AgregadoSesión

**Criterios de Aceptación**:
- [ ] Formulario de consentimiento se muestra antes de comenzar
- [ ] Se requieren los 3 tipos de consentimiento
- [ ] Entradas de auditoría creadas con ip/user_agent
- [ ] Sesión no puede ser ACTIVA sin consentimientos

---

### REGLA-BACKEND-03: Transiciones de Estado del Candidato

**Descripción**: El estado del candidato sigue progresión monótona (sin retroceso).

**Condición**: Candidato completa acciones o evaluación concluye

**Acción**:
```
REGISTRADO → EVALUANDO → EVALUADO → (APROBADO | RECHAZADO)
                                  └→ ARCHIVADO (después 30d)
```

1. Nuevo candidato → REGISTRADO
2. Entra a sesión → EVALUANDO (primer mensaje enviado/recibido)
3. Screening completado → EVALUADO
4. Puntuación disponible → APROBADO (≥75) o RECHAZADO (<50) o REVISAR
5. Después inactividad + reenganche por correo → puede volver a EVALUANDO
6. Nunca retrocede (e.g., APROBADO → EVALUANDO no permitido)

**Consecuencia**:
- Seguimiento claro de progreso
- Permite filtrado de dashboard (mostrar RECHAZADOS por separado)
- Previene problemas de integridad de datos

**Origen**: functional-design.md § Ciclo de Vida Candidato  
**Agregado Afectado**: AgregadoCandidato

**Criterios de Aceptación**:
- [ ] Enum de estado cumple transiciones permitidas
- [ ] Sin transiciones hacia atrás (prueba valida)
- [ ] Candidatos ARCHIVADOS inmutables
- [ ] Registro de auditoría de todas las transiciones

---

### REGLA-BACKEND-04: Ordenamiento e Inmutabilidad de Mensajes

**Descripción**: Los mensajes de screening se ordenan cronológicamente e son inmutables.

**Condición**: Cualquier mensaje enviado/recibido en screening

**Acción**:
1. Cada mensaje recibe id único + número de secuencia
2. Mensajes almacenados en orden cronológico (fecha DESC)
3. Una vez creado, contenido del mensaje es SOLO LECTURA
4. Eliminaciones no permitidas (solo soft-delete si es necesario)

**Consecuencia**:
- Registro de auditoría es confiable (sin ediciones retroactivas)
- Transcripción es legalmente defendible
- Permite revisión de equidad (sin seleccionar evidencia)

**Origen**: Requisito de cumplimiento (LGPD § 6)  
**Agregado Afectado**: AgregadoScreening

**Criterios de Aceptación**:
- [ ] Mensaje.creada_en inmutable (restricción base de datos)
- [ ] Sin operaciones UPDATE en contenido
- [ ] Solo soft-delete (bandera es_eliminada, sin hard delete)
- [ ] Pruebas verifican ordenamiento con inserts concurrentes

---

### REGLA-BACKEND-05: Escalada de Intento Jailbreak

**Descripción**: Los intentos de jailbreak se cuentan y escalan a terminación.

**Condición**: Screening detecta inyección de prompt o anomalía de seguridad

**Acción**:
1. BotEngine escanea mensaje contra 20+ patrones jailbreak
2. Si detectado:
   - BAJO: registrar intento, continuar (usuario advertido)
   - MEDIO: registrar, continuar, incrementar contador
   - ALTO: registrar, bloquear respuesta, incrementar contador (usuario ve disculpa)
   - CRÍTICO: registrar, terminar screening inmediatamente
3. Después 3 intentos ALTO/MEDIO → auto-terminar screening
4. Crear entrada de AuditoríaEvento para cada intento

**Consecuencia**:
- Seguridad: Protege contra ataques de inyección de prompt
- Cumplimiento: Mantiene registro de auditoría
- UX: Manejo gracioso (usuario sabe qué pasó)

**Origen**: Requisito de Seguridad (§ 3.2.1)  
**Agregado Afectado**: AgregadoScreening

**Criterios de Aceptación**:
- [ ] Contador de intentos_jailbreak incrementa correctamente
- [ ] Después 3 intentos, screening falla auto
- [ ] Registros de auditoría para cada intento ALTO/MEDIO
- [ ] Pruebas contra patrones OWASP Top 10

---

### REGLA-BACKEND-06: Detección y Límites de Fuera del Tema

**Descripción**: Preguntas fuera de tema se redirigen; demasiadas violaciones auto-terminan.

**Condición**: Screening detecta mensaje fuera de tema

**Acción**:
1. Prompt del sistema incluye: "Si candidato pregunta fuera de tema, redirigir amablemente"
2. Respuesta del BotEngine incluye marcador de redirección
3. Contar violaciones (máx 3 por screening)
4. Después 3 violaciones → auto-terminar screening (estado FALLIDO)
5. Registro de auditoría: contador_fuera_tema

**Consecuencia**:
- Mantiene calidad del screening (respuestas en tema)
- Justo: candidatos que se desvían 3x se marcan justamente
- Gracioso: permite cierta flexibilidad antes de terminación

**Origen**: Mejores prácticas de screening  
**Agregado Afectado**: AgregadoScreening

**Criterios de Aceptación**:
- [ ] contador_fuera_tema rastreado
- [ ] Después 3 violaciones, screening auto-termina
- [ ] Entradas de auditoría registradas
- [ ] Pruebas verifican mensajes de redirección

---

### REGLA-BACKEND-07: Cumplimiento de Presupuesto de Tokens

**Descripción**: Las conversaciones están limitadas por presupuesto de tokens (control de costo).

**Condición**: Cualquier mensaje intercambiado en screening

**Acción**:
1. Screening inicializado con presupuesto_tokens = 2000 tokens
2. Antes de llamar API Claude, verificar: tokens_usados + tokens_estimados_nuevos ≤ presupuesto
3. Si presupuesto excedido:
   - Truncar conversación (mensajes antiguos removidos, resumidos)
   - Re-estimar contador tokens
   - Proceder solo si cabe
4. Si no cabe: devolver respuesta degradada
5. Rastrear tokens_usados continuamente (propósitos auditoría)

**Consecuencia**:
- Previsibilidad de costos (sin facturas API descontroladas)
- Justo: todos candidatos obtienen presupuesto similar
- Degradación gracioso (usuarios entienden límites)

**Origen**: Restricción financiera (requisito economía unitaria)  
**Agregado Afectado**: AgregadoScreening

**Criterios de Aceptación**:
- [ ] tokens_usados incrementa con precisión (±5%)
- [ ] Desbordamiento de presupuesto prevenido
- [ ] Truncamiento de conversación preserva significado
- [ ] Registro de auditoría de uso de tokens

---

### REGLA-BACKEND-08: Detección de Inactividad y Pausa

**Descripción**: Las sesiones se auto-pausan después 5 minutos de inactividad.

**Condición**: Sin entrada de usuario por 5+ minutos

**Acción**:
1. Backend rastraea última_actividad_en marca de tiempo
2. Trabajo en segundo plano (cada 2 min): verifica: ahora - última_actividad_en > 5min
3. Si inactiva >5min:
   - Transición Sesión a PAUSADA (si fue ACTIVA)
   - Notificar candidato: "Su sesión se ha pausado. Haga clic para reanudar."
   - Limpiar contexto de conversación (ahorro de costo)
4. Candidato puede reanudar dentro 24h (re-establecer contexto)
5. Después 24h PAUSADA → auto-abandonar

**Consecuencia**:
- Ahorro de costos (libera recursos)
- Respeta tiempo candidato (reconoce pausa)
- Justicia: todos candidatos reciben misma regla pausa
- Cumplimiento LGPD (fin de sesión claro)

**Origen**: Optimización de costos + mejor práctica UX  
**Agregado Afectado**: AgregadoSesión

**Criterios de Aceptación**:
- [ ] Trabajo inactividad se ejecuta correctamente
- [ ] Sesión transiciona a PAUSADA en 5min
- [ ] Candidato notificado (correo/dashboard)
- [ ] Después 24h PAUSADA → ABANDONADA

---

### REGLA-BACKEND-09: Inmutabilidad de Evaluación

**Descripción**: Una vez completada evaluación, no puede ser modificada.

**Condición**: Evaluación transiciona a estado COMPLETADA

**Acción**:
1. Durante evaluación (EN_PROGRESO):
   - Puntuación, recomendación, retroalimentación pueden actualizarse (re-puntuación Claude)
   - Citas siendo recolectadas
2. Cuando se publica evento evaluación_completada:
   - Estado → COMPLETADA
   - Agregado se vuelve SOLO LECTURA
   - No más mutaciones permitidas
3. Si re-evaluación necesaria:
   - Crear NUEVO registro Evaluación
   - Vincular ambas evaluaciones (versión histórica)
   - Usar evaluación más nueva para decisión final

**Consecuencia**:
- Registro de auditoría inmutable (legalmente defendible)
- Justo: candidatos no pueden sorprenderse por puntuaciones cambiadas
- Permite apelaciones (comparar v1 vs v2)

**Origen**: Requisito de cumplimiento + equidad  
**Agregado Afectado**: AgregadoEvaluación

**Criterios de Aceptación**:
- [ ] Restricción base de datos: Evaluación.estado COMPLETADA = inmutable
- [ ] Pruebas verifican sin UPDATEs después COMPLETADA
- [ ] Re-evaluación crea registro nuevo con versionado
- [ ] Registros de auditoría rastrean historial versiones

---

### REGLA-BACKEND-10: Lógica de Recomendación

**Descripción**: Puntuación mapea determinísticamente a recomendación.

**Condición**: Puntuación de evaluación completada

**Acción**:
```
SI puntuación >= 75:
    recomendación = APROBADO
SINO SI puntuación < 50:
    recomendación = RECHAZADO
SINO (50 <= puntuación < 75):
    recomendación = REVISAR
```

1. Recomendación calculada inmediatamente después puntuación
2. Inmutable (igual que puntuación)
3. REVISAR dispara cola HITL (revisión humana)
4. APROBADO/RECHAZADO evitan HITL (a menos flagueado por equidad)

**Consecuencia**:
- Determinístico: sin ambigüedad en umbrales
- Justo: mismas reglas aplican a todos candidatos
- Camino de decisión claro (HITL sabe cuáles van a revisión)

**Origen**: functional-design.md § Umbrales Puntuación  
**Agregado Afectado**: AgregadoEvaluación

**Criterios de Aceptación**:
- [ ] Mapeo puntuación-a-recomendación testeado
- [ ] Casos límite (49, 50, 74, 75) verificados
- [ ] Recomendación coincide con campo recomendación
- [ ] Casos REVISAR rutean a cola HITL

---

### REGLA-BACKEND-11: Ciclo de Vida de Campaña

**Descripción**: Campañas tienen ciclo de vida estricto con control de versiones.

**Condición**: Campaña creada, publicada o archivada

**Acción**:
```
BORRADOR → PUBLICADA → (PAUSADA ↔ PUBLICADA)* → ARCHIVADA
```

1. Nueva campaña → BORRADOR
2. Admin revisa → PUBLICADA (habilita screenings)
3. Admin puede PAUSAR (detiene nuevos screenings) y reanudar
4. Después contratación completa → ARCHIVADA (solo lectura, sin nuevos screenings)
5. Nunca eliminar campañas (registro de auditoría)

**Consecuencia**:
- Gobernanza clara (quién puede screenear con qué campaña)
- Registro de auditoría (rastrear versiones de campaña)
- Justo: todos candidatos en misma campaña usan misma versión rúbrica

**Origen**: Requisito gestión de campañas  
**Agregado Afectado**: AgregadoCampaña

**Criterios de Aceptación**:
- [ ] Campaign.estado cumple máquina de estados
- [ ] Campañas archivadas inmutables
- [ ] Campañas publicadas vinculadas a sesiones screening
- [ ] Registros auditoría rastrean cambios estado

---

### REGLA-BACKEND-12: Inmutabilidad de Rúbrica y Versionado

**Descripción**: Rúbrica es inmutable una vez publicada; cambios crean versión nueva.

**Condición**: Campaña publicada con rúbrica O rúbrica actualizada

**Acción**:
1. Mientras campaña BORRADOR: rúbrica puede editarse
2. Cuando campaña PUBLICADA: rúbrica.versión incrementada, bloqueada
3. Para cambiar rúbrica: crear versión nueva (rúbrica_versión + 1)
4. Screenings antiguos usan versión antigua rúbrica (no se cambia retroactivamente)
5. Nuevos screenings usan versión nueva rúbrica
6. Evaluación almacena versión_rúbrica para trazabilidad

**Consecuencia**:
- Justo: misma versión rúbrica aplica a cohorte de candidatos
- Registro auditoría: rastrear qué versión puntuó qué candidatos
- Sin cambios puntuación retroactivos (defendible)

**Origen**: Requisito cumplimiento + equidad  
**Agregado Afectado**: AgregadoCampaña

**Criterios de Aceptación**:
- [ ] Versionado de rúbrica cumplido en código
- [ ] Versiones antiguas preservadas
- [ ] Screening.versión_rúbrica y Evaluación.versión_rúbrica coinciden
- [ ] Pruebas verifican inmutabilidad

---

### REGLA-BACKEND-13: Rastreo de Consentimiento y Registro de Auditoría

**Descripción**: Todos cambios de consentimiento auditados con metadatos.

**Condición**: Candidato da o revoca consentimiento

**Acción**:
1. Consentimiento.dado_en = marca de tiempo, con dirección_ip + user_agent capturados
2. Si candidato revoca consentimiento:
   - Consentimiento.revocado_en = marca de tiempo
   - Consentimiento.estado → REVOCADO
   - Crear EntradaAuditoriaConsentimiento (acción=REVOCADO, ip, user_agent)
   - Detener cualquier correo reenganche pendiente
   - Marcar PII como redactada
3. Registro auditoría inmutable (append-only)

**Consecuencia**:
- Cumplimiento LGPD (rastreo de consentimiento)
- Defendible: puede probar candidato consintió o revocó
- Gobernanza de datos: saber quién consintió cuándo

**Origen**: LGPD Artículo 8  
**Agregado Afectado**: AgregadoConsentimiento

**Criterios de Aceptación**:
- [ ] Consentimiento.dado_en/revocado_en inmutable
- [ ] Registro auditoría append-only
- [ ] IP/user_agent capturados en consentimiento
- [ ] Revocación bloquea procesamiento descendente

---

### REGLA-BACKEND-14: Estrategia de Invalidación de Memoria

**Descripción**: Datos en memoria caducan e invalidados en actualizaciones de origen.

**Condición**: Rúbrica actualizada O campaña publicada

**Acción**:
1. Entradas de memoria tienen TTL = 3600s (1 hora default)
2. En evento CampaignPublished:
   - Invalidar todas entradas memoria para ese id_campaña
   - Limpiar memoria de rúbrica
3. Trabajo background: eliminar entradas memoria expiradas (una vez por hora)
4. Si cache miss: traer de BD, almacenar en memoria, devolver

**Consecuencia**:
- Rendimiento: rúbricas en memoria evitan hits BD
- Consistencia: memoria antigua caduca automáticamente
- Event-driven: invalidación en cambio de origen

**Origen**: Requisito rendimiento (p95 < 500ms)  
**Agregado Afectado**: AgregadoEntradaMemoria

**Criterios de Aceptación**:
- [ ] TTL memoria cumplido
- [ ] Invalidación event-driven funcionando
- [ ] Trabajo limpieza background ejecutándose
- [ ] Tasa de hit memoria >85% rastreada

---

### REGLA-BACKEND-15: Publicación de Eventos y Confiabilidad

**Descripción**: Eventos publicados a Redis Pub/Sub con lógica de reintento.

**Condición**: Cualquier evento significativo dominio (SesiónIniciada, EvaluaciónCompletada, etc.)

**Acción**:
1. Servicio publica evento a Redis Pub/Sub (tema = tipo_evento)
2. Evento almacenado en EntradaEvento (estado = PENDIENTE)
3. Suscriptores (e.g., ServicioHITL) consumen evento
4. En éxito: EntradaEvento.estado = PUBLICADA
5. En fallo: reintentar hasta 5 veces (backoff exponencial: 1s, 2s, 4s, 8s, 16s)
6. Después 5 fallos: EntradaEvento.estado = FALLIDA, alerta ops

**Consecuencia**:
- Confiable: eventos eventualmente entregados
- Auditable: todos eventos registrados
- Desacoplado: publicadores no bloquean suscriptores

**Origen**: Requisito arquitectura event-driven  
**Agregado Afectado**: AgregadoEntradaEventoDominio

**Criterios de Aceptación**:
- [ ] Eventos publicados a Redis
- [ ] Registros de EntradaEvento creados
- [ ] Lógica reintento funcionando (prueba con fallo simulado)
- [ ] Eventos fallidos alertables

---

## 📊 Matriz de Trazabilidad de Reglas de Negocio

| Regla | Agregado | Evento | Criterios de Aceptación |
|---|---|---|---|
| REGLA-BACKEND-01 | Sesión | SesiónIniciada, SesiónCompletada | Máquina de estados cumplida |
| REGLA-BACKEND-02 | Consentimiento | ConsentimientoOtorgado | Formulario bloquea progresión |
| REGLA-BACKEND-03 | Candidato | CambioEstadoCandidato | Transiciones monótonas |
| REGLA-BACKEND-04 | Screening | MensajeIntercambiado | Mensajes inmutables |
| REGLA-BACKEND-05 | Screening | JailbreakDetectado | Auto-terminar en 3 |
| REGLA-BACKEND-06 | Screening | ScreeningCompletado | Auto-terminar en 3 violaciones |
| REGLA-BACKEND-07 | Screening | MensajeIntercambiado | Presupuesto no excedido |
| REGLA-BACKEND-08 | Sesión | SesiónPausada | Auto-pausa en 5min |
| REGLA-BACKEND-09 | Evaluación | EvaluaciónCompletada | Inmutable después COMPLETADA |
| REGLA-BACKEND-10 | Evaluación | EvaluaciónCompletada | Recomendación determinística |
| REGLA-BACKEND-11 | Campaña | CampaignPublicada | Máquina de estados cumplida |
| REGLA-BACKEND-12 | Campaña | CampaignActualizada | Versionado de rúbrica inmutable |
| REGLA-BACKEND-13 | Consentimiento | ConsentimientoRevocado | Registro auditoría append-only |
| REGLA-BACKEND-14 | Memoria | CampaignActualizada | TTL cumplido, invalidación disparada |
| REGLA-BACKEND-15 | EntradaEvento | (todos) | Lógica reintento con backoff |

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 10 Reglas de Negocio documentadas con trazabilidad de origen
- [x] Cada regla tiene secciones Condición, Acción, Consecuencia
- [x] Propiedad de agregado clara para cada regla
- [x] Disparadores de eventos identificados
- [x] Criterios de aceptación para cada regla definidos
- [x] Matriz de trazabilidad completa

---

**Generado**: 2026-05-27  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 1 - Reglas de Negocio  
**Estado**: ✅ COMPLETADA
