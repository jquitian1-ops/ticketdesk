# Unit 2: Fundamentos Backend — Actividad 1: Flujos E2E (Lógica de Negocio)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 1 - Diseño Funcional: Modelo de Lógica de Negocio (Flujos De Extremo a Extremo)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**5 Flujos de Extremo a Extremo** describiendo procesos de negocio completos con transiciones de estado, manejo de errores y publicación de eventos.

---

## 🎯 Flujo 1: Crear Sesión y Obtener Consentimiento

**Duración**: 3-5 minutos  
**Actores**: Candidato, API Backend, ServicioConsentimiento  
**Disparador**: Candidato hace clic "Iniciar Screening" desde página de campaña  

### Pre-condiciones
- Campaña es PUBLICADA
- Candidato es REGISTRADO en sistema
- Conexión de red activa

### Pasos

1. **POST /api/campañas/{id_campaña}/sesiones**
   - Solicitud: `{ id_candidato, metadatos: { dispositivo, ip, ubicación } }`
   - Backend crea agregado Sesión
   - Sesión.estado = CREADA
   - Sesión.creada_en = ahora (inmutable)
   - Devuelve: `{ id_sesión, url_formulario_consentimiento }`

2. **Cargar Formulario Consentimiento (GET /api/sesiones/{id_sesión}/consentimiento)**
   - Devuelve: DocumentoConsentimiento (3 tipos: PROCESAMIENTO, GRABACIÓN, ANALÍTICA)
   - Frontend muestra formulario con texto legal
   - Casillas requeridas para los 3

3. **Candidato Revisa y Acepta**
   - Frontend muestra:
     - "Acepto procesamiento de datos" (requerido)
     - "Acepto ser grabado" (requerido)
     - "Acepto analítica" (recomendado)
   - Candidato debe marcar todos
   - Hacer clic en botón "Acepto"

4. **POST /api/sesiones/{id_sesión}/consentimiento**
   - Solicitud: `{ tipos_consentimiento: [PROCESAMIENTO, GRABACIÓN, ANALÍTICA], dirección_ip, user_agent }`
   - ServicioConsentimiento crea 3 agregados Consentimiento (uno por tipo)
   - Consentimiento.estado = OTORGADO
   - Consentimiento.dado_en = ahora
   - Capturar metadatos (dirección_ip, user_agent)
   - Publicar evento: **ConsentimientoOtorgado** (tema: consentimiento.otorgado)
   - Devuelve: `{ ids_consentimiento, consentimiento_dado_en }`

5. **Transicionar Sesión a ACTIVA**
   - POST /api/sesiones/{id_sesión}/iniciar
   - Sesión.estado = CREADA → ACTIVA
   - Sesión.iniciada_en = ahora
   - Publicar evento: **SesiónIniciada** (tema: sesión.iniciada)
   - Devuelve: `{ id_sesión, screening_listo }`

### Camino de Éxito
- Candidato ve ventana de chat
- Sesión.estado = ACTIVA
- Temporizador de inactividad comienza

### Caminos de Error

**Error 1: Campaña No Encontrada**
```
Paso 1: Búsqueda de campaña falla
→ Devolver 404 No Encontrada
→ Frontend muestra: "Campaña no disponible"
```

**Error 2: Consentimiento No Completo**
```
Paso 3: Candidato desmarca casilla
→ Botón "Acepto" deshabilitado
→ Frontend muestra: "Por favor, acepte todos los requisitos"
```

**Error 3: Fallo de Red Durante Consentimiento**
```
Paso 4: POST falla (timeout)
→ Frontend muestra: "Error de conexión, intente nuevamente"
→ Botón Reintentar habilitado (POST idempotente)
```

### Post-condiciones
- Sesión.estado = ACTIVA
- 3 registros Consentimiento existen (PROCESAMIENTO, GRABACIÓN, ANALÍTICA todos OTORGADOS)
- Eventos publicados: SesiónIniciada, ConsentimientoOtorgado
- Candidato puede iniciar screening

---

## 🎯 Flujo 2: Intercambio de Mensaje en Screening

**Duración**: 2-8 horas (según campaña)  
**Actores**: Candidato, MotorBot, ServicioScreening, ServicioEvaluación  
**Disparador**: Candidato escribe mensaje en chat  

### Pre-condiciones
- Sesión es ACTIVA
- Screening iniciado (tiene mensaje de apertura del bot)
- Candidato tiene Consentimiento válido (PROCESAMIENTO = OTORGADO)

### Pasos

1. **Candidato Escribe Mensaje**
   - Frontend: Usuario escribe texto en entrada de chat
   - Envía: POST /api/conversaciones/{id_conversación}/mensajes
   - Solicitud: `{ rol: "usuario", contenido, marca_tiempo }`

2. **Validación Backend**
   - Parsear mensaje (validación UTF-8)
   - Verificar longitud (máx 5000 caracteres)
   - Sanitizar (sin etiquetas HTML/script)
   - Detectar idioma (textblob)
   - Si no es inglés: traducir al inglés para Claude (mantener original para mostrar)

3. **Detección de Jailbreak**
   - MotorBot.escanear_jailbreak(contenido)
   - Verificar contra 20+ patrones regex:
     - Marcadores inyección prompt ("Ignora anterior", "Ahora eres", etc.)
     - Trucos codificación (base64, escapes hexadecimales)
     - Manipulación de tokens ("prompt del sistema", "anulación de instrucciones")
     - Puntuación/símbolos excesivos (detección de anomalía)
   - Devolver: nivel_riesgo (BAJO, MEDIO, ALTO, CRÍTICO)

4. **Evaluación de Riesgo**
   ```
   SI nivel_riesgo == CRÍTICO:
       → Bloquear respuesta, terminar screening
       → Screening.estado = FALLIDO
       → Publicar evento: ScreeningFallido
       → Devolver a candidato: "Su sesión terminó por actividad sospechosa"
   
   SINO SI nivel_riesgo == ALTO:
       → Incrementar Screening.intentos_jailbreak
       → Bloquear respuesta, mostrar advertencia
       → Devolver a candidato: "Esa solicitud viola nuestras políticas"
   
   SINO SI nivel_riesgo == MEDIO:
       → Incrementar Screening.intentos_jailbreak
       → Registrar intento (auditoría)
       → Continuar (con advertencia)
   
   SINO:
       → Continuar normalmente
   ```

5. **Verificación de Presupuesto de Tokens**
   ```
   tokens_estimados = estimar_tokens(contenido_mensaje)
   SI Screening.tokens_usados + tokens_estimados > presupuesto_tokens:
       → Truncar conversación (mensajes antiguos removidos, resumidos)
       → Re-estimar contador
       SI todavía excede presupuesto:
           → Devolver respuesta degradada: "Estoy experimentando límites, intente después"
           → Publicar evento: PresupuestoTokensExcedido
   ```

6. **Llamar a Claude API (Streaming)**
   - MotorBot construye prompt_sistema (rol, contexto laboral, rúbrica, instrucciones)
   - prompt_sistema incluye: "Si candidato pregunta fuera de tema, redirigir..."
   - mensajes = [... historial conversación ..., { rol: "usuario", contenido }]
   - Llamar: cliente.mensajes.crear(modelo="claude-3-5-sonnet", stream=True, mensajes, sistema=prompt_sistema)
   - Recopilar stream de tokens (SSE/WebSocket en tiempo real a frontend)
   - Razón de parada: fin_turno o máx_tokens o secuencia_parada

7. **Detectar Fuera del Tema (Basado en Instrucción)**
   - Monitorear respuesta para marcadores de redirección:
     - "Volvamos a...", "Eso está fuera de mi alcance...", "Estoy aquí para ayudar con..."
   - Si detectado: incrementar Screening.contador_fuera_tema
   - Después 3 violaciones: auto-terminar (Screening.estado = FALLIDO)

8. **Almacenar Par de Mensajes**
   - Crear agregado Mensaje (usuario + asistente, ambos inmutables)
   - Mensaje.rol = "usuario" | "asistente"
   - Mensaje.contenido = (idioma original)
   - Mensaje.tokens_usados = estimados + reales de API
   - Mensaje.marca_tiempo = ahora (inmutable)
   - Screening.tokens_usados += mensaje.tokens_usados
   - Persistir ambos mensajes (transaccional)

9. **Verificar Continuación**
   ```
   SI Screening.intentos_jailbreak >= 3:
       → Screening.estado = FALLIDO
       → Publicar evento: ScreeningCompletado
       → Devolver: "Su screening ha terminado"
   
   SINO SI Screening.contador_fuera_tema >= 3:
       → Screening.estado = FALLIDO
       → Publicar evento: ScreeningCompletado
       → Devolver: "Su screening ha terminado"
   
   SINO SI todas_preguntas_respondidas_O_timeout_alcanzado:
       → Screening.estado = COMPLETADO
       → Publicar evento: ScreeningCompletado
       → Devolver: "¡Gracias! Su screening completó. Lo revisaremos y contactaremos."
   
   SINO:
       → Continuar (usuario puede enviar próximo mensaje)
   ```

10. **Publicar Evento**
    - Evento: **MensajeIntercambiado**
    - Carga útil: { id_sesión, id_mensaje, rol, tokens_usados, marca_tiempo, jailbreak_detectado }

### Camino de Éxito
- Mensaje almacenado (inmutable)
- Respuesta asistente transmitida a frontend
- Tokens rastreados
- Screening continúa (o completa si todas preguntas respondidas)

### Caminos de Error

**Error 1: Timeout API Claude**
```
Paso 6: cliente.mensajes.crear timeout (>10s)
→ Circuito breaker se dispara
→ Devolver respuesta degradada: "Estoy experimentando retrasos..."
→ Publicar evento: ModoDesgraduado
→ Reintentar con respuesta en caché
```

**Error 2: Mensaje Contiene Jailbreak (ALTO)**
```
Paso 4: Jailbreak detectado
→ Incrementar intentos_jailbreak (ahora = 1)
→ No llamar Claude
→ Devolver: "Esa solicitud viola nuestras políticas. Por favor, manténgase en tema."
→ Después 3 intentos → Screening.estado = FALLIDO
```

**Error 3: Presupuesto de Tokens Excedido**
```
Paso 5: tokens_usados exceede presupuesto
→ Truncar conversación
→ Devolver respuesta degradada
→ Candidato ve: "Estoy experimentando límites, intente después"
→ Solicitarle enviar lo que tiene
```

**Error 4: Mensaje Mal Formado**
```
Paso 2: Sanitización falla
→ Devolver 400 Solicitud Inválida
→ Frontend muestra: "Formato de mensaje inválido"
```

### Post-condiciones
- Par de mensajes persistido (usuario + asistente, ambos inmutables)
- Screening.tokens_usados incrementado
- Eventos publicados (MensajeIntercambiado, posiblemente ScreeningCompletado)
- Sesión.última_actividad_en = ahora (temporizador inactividad reiniciado)

---

## 🎯 Flujo 3: Completar Screening y Disparar Evaluación

**Duración**: <1 segundo  
**Actores**: ServicioScreening, ServicioEvaluación, BarraEventos  
**Disparador**: Evento ScreeningCompletado publicado  

### Pre-condiciones
- Estado screening = COMPLETADO (o FALLIDO con 3 jailbreaks)
- Todos mensajes almacenados
- Transcripción capturada

### Pasos

1. **Generar Transcripción**
   - Recopilar todos mensajes (usuario + asistente) de Screening
   - Convertir a estructura JSON:
     ```json
     {
       "id_sesión": "...",
       "id_screening": "...",
       "creada_en": "...",
       "completada_en": "...",
       "duración_segundos": 3600,
       "cantidad_mensajes": 15,
       "mensajes": [
         { "rol": "usuario", "contenido": "...", "marca_tiempo": "..." },
         { "rol": "asistente", "contenido": "...", "marca_tiempo": "..." }
       ],
       "metadatos": { "tokens_usados": 1850, "idioma": "es", "intentos_jailbreak": 0 }
     }
     ```

2. **Cargar en S3**
   - Clave S3: `transcripciones/{id_sesión}/{id_screening}.json`
   - Encriptación: clave KMS (en reposo + en tránsito)
   - Versionado: habilitado
   - Ciclo de vida: retención 7 años (cumplimiento), después eliminar
   - Crear AuditoríaEvento: ACCIÓN=TRANSCRIPCIÓN_CARGADA

3. **Crear Agregado Transcripción**
   - Generar URL firmada (caduca 24h)
   - Transcripción.id_sesión = id_sesión
   - Transcripción.url_audio = s3_url (para grabaciones de audio futuro)
   - Transcripción.url_texto = s3_url (transcripción JSON)
   - Transcripción.creada_en = ahora
   - Publicar evento: **TranscripciónCreada**

4. **Publicar Evento ScreeningCompletado**
   - Evento: **ScreeningCompletado**
   - Tema: screening.completado
   - Carga útil:
     ```json
     {
       "id_screening": "...",
       "id_sesión": "...",
       "id_candidato": "...",
       "id_campaña": "...",
       "estado": "COMPLETADO",
       "cantidad_mensajes": 15,
       "tokens_usados": 1850,
       "url_transcripción": "s3://...",
       "completada_en": "2026-05-27T14:30:00Z"
     }
     ```

5. **Suscriptores Consumen Evento**
   - ServicioEvaluación se suscribe a screening.completado
   - Recibe evento ScreeningCompletado
   - Dispara inicio de Evaluación (ver Flujo 4)

### Camino de Éxito
- Screening marcado COMPLETADO (inmutable)
- Transcripción almacenada en S3
- Evento publicado
- ServicioEvaluación comienza evaluación automáticamente

### Caminos de Error

**Error 1: Carga S3 Falla**
```
Paso 2: S3.poner_objeto timeout
→ Reintentar (hasta 3 veces con backoff exponencial)
→ Si todos fallan: EntradaEvento.estado = FALLIDA, alerta ops
→ Screening.estado permanece COMPLETADO (no bloquear)
→ Recuperación manual: ops puede reintentar carga
```

**Error 2: Publicación de Evento Falla**
```
Paso 4: Redis Pub/Sub timeout
→ EntradaEvento.estado = PENDIENTE
→ Trabajo de reintento se ejecuta (cada 5 min)
→ Después 5 fallos: EntradaEvento.estado = FALLIDA
```

### Post-condiciones
- Screening.estado = COMPLETADO (inmutable)
- Transcripción en S3 (encriptada, versionada, retención 7 años)
- Evento ScreeningCompletado publicado
- ServicioEvaluación disparado (asincrónico)

---

## 🎯 Flujo 4: Evaluar Screening y Generar Puntuación

**Duración**: 5-10 segundos  
**Actores**: ServicioEvaluación, API Claude, ExtractorCitas, CalculadorEquidad  
**Disparador**: Evento ScreeningCompletado  

### Pre-condiciones
- Screening completado + transcripción disponible
- Campaña publicada con rúbrica
- ServicioEvaluación escuchando tema screening.completado

### Pasos

1. **Cargar Rúbrica (En Memoria Caché)**
   - ServicioEvaluación recibe evento ScreeningCompletado
   - Consultar: Rúbrica para id_campaña + versión_rúbrica
   - Verificar caché Redis (TTL = 1h)
   - Si acierto caché: usar rúbrica en caché (sin hit BD)
   - Si fallo caché: cargar de BD, cachear en Redis
   - Rúbrica contiene: dimensiones[], criterios_puntuación, pesos

2. **Llamar API Claude para Puntuación**
   - Construir prompt:
     ```
     Eres un reclutador experto evaluando screening de candidato.
     
     Dimensiones Rúbrica:
     - Habilidades Técnicas (peso: 40%)
     - Comunicación (peso: 30%)
     - Resolución de Problemas (peso: 20%)
     - Liderazgo (peso: 10%)
     
     Criterios Puntuación:
     - 90-100: Excepcional, supera expectativas
     - 75-89: Fuerte, cumple todos requisitos
     - 50-74: Adecuado, algunas brechas
     - <50: Débil, brechas significativas
     
     Transcripción:
     [insertar mensajes de screening]
     
     Proporcionar respuesta JSON:
     {
       "puntuación_general": 85,
       "puntuaciones_dimensión": {
         "Habilidades Técnicas": { "puntuación": 88, "evidencia": "..." },
         "Comunicación": { "puntuación": 82, "evidencia": "..." },
         ...
       },
       "recomendación": "APROBADO",
       "retroalimentación": {
         "fortalezas": [...],
         "mejoras": [...],
         "justificación": "..."
       }
     }
     ```
   - Llamar: cliente.mensajes.crear(modelo="claude-3-5-sonnet", response_format={"type": "json_object"}, ...)
   - Parsear respuesta JSON
   - Validar: puntuación ∈ [0, 100], recomendación ∈ {APROBADO, RECHAZADO, REVISAR}

3. **Extraer Citas (Coincidencia Difusa)**
   - ExtractorCitas recibe puntuaciones_dimensión con cadenas de evidencia
   - Para cada cadena de evidencia: coincidencia difusa contra mensajes transcripción
   - Biblioteca RapidFuzz: encontrar mensaje mejor coincidencia (confianza >70%)
   - Agregado Cita:
     ```
     Cita {
       id_evaluación: UUID,
       fragmento_texto: str (máx 200 caracteres),
       marca_tiempo_origen: datetime,
       confianza: float (0.7-1.0)
     }
     ```
   - Almacenar todas citas (inmutables)

4. **Calcular Puntuación Equidad**
   - CalculadorEquidad analiza retroalimentación para señales sesgo
   - Verificar patrones:
     - Sesgo género: palabras como "asertivo", "agresivo" (lenguaje generizado)
     - Sesgo edad: "joven", "energético", "sobrecalificado"
     - Señales demográficas en retroalimentación
   - Agregado PuntuaciónEquidad:
     ```
     PuntuaciónEquidad {
       id_evaluación: UUID,
       riesgo_sesgo_general: float (0.0-1.0),
       riesgo_por_dimensión: Mapa[dimensión → float],
       banderas: Lista[BanderaSesgó]
     }
     ```
   - Si riesgo_sesgo > 0.3: flagear para revisión HITL (anular recomendación a REVISAR)

5. **Calcular Recomendación Final**
   ```
   puntuación = promedio ponderado puntuaciones_dimensión
   
   SI riesgo_sesgo > 0.3:
       recomendación = REVISAR (forzar HITL)
   SINO SI puntuación >= 75:
       recomendación = APROBADO
   SINO SI puntuación < 50:
       recomendación = RECHAZADO
   SINO:
       recomendación = REVISAR
   ```

6. **Crear Agregado Evaluación**
   - Agregado Evaluación (inmutable):
     ```
     Evaluación {
       id: UUID,
       id_sesión: UUID,
       id_screening: UUID,
       id_campaña: UUID,
       puntuación: 85,
       recomendación: APROBADO,
       confianza: 0.92,
       puntuaciones_dimensión: {...},
       citas: [Cita, Cita, ...],
       puntuación_equidad: {...},
       estado: COMPLETADA,
       completada_en: ahora
     }
     ```
   - Persistir a BD (transaccional con citas)

7. **Publicar Evento EvaluaciónCompletada**
   - Evento: **EvaluaciónCompletada**
   - Tema: evaluación.completada
   - Carga útil:
     ```json
     {
       "id_evaluación": "...",
       "id_sesión": "...",
       "id_candidato": "...",
       "puntuación": 85,
       "recomendación": "APROBADO",
       "completada_en": "2026-05-27T14:35:00Z"
     }
     ```

### Camino de Éxito
- Evaluación creada (COMPLETADA, inmutable)
- Citas extraídas (>85% precisión)
- Equidad calculada
- Evento publicado

### Caminos de Error

**Error 1: API Claude Falla**
```
Paso 2: API devuelve error
→ Reintentar hasta 3 veces
→ Si todos fallan: Evaluación.estado = FALLIDA
→ EntradaEvento.estado = FALLIDA
→ Publicar evento EvaluaciónFallida
→ Alerta ops
```

**Error 2: Cálculo Equidad Muestra Sesgo Alto**
```
Paso 4: riesgo_sesgo = 0.45
→ Forzar recomendación = REVISAR
→ Flagear para HITL con alerta sesgo
→ Auditor notificado
```

**Error 3: Extracción Cita Falla**
```
Paso 3: Sin coincidencias encontradas
→ confianza = 0.0
→ Aún completar evaluación
→ Flagear en verificación equidad (evidencia faltante)
→ Forzar REVISAR si confianza demasiado baja
```

### Post-condiciones
- Evaluación.estado = COMPLETADA (inmutable)
- Citas extraídas y almacenadas
- Puntuación equidad calculada
- Evento EvaluaciónCompletada publicado
- Estado candidato actualizado a EVALUADO
- Si recomendación = REVISAR: dispara cola HITL (Unit 6)

---

## 🎯 Flujo 5: Auto-Expirar Sesiones Inactivas

**Duración**: < 1 segundo (por sesión)  
**Actores**: TrabajoExpiracióSesión, ServicioSesión, BarraEventos  
**Disparador**: Trabajo background (cada 2 minutos)  

### Pre-condiciones
- Trabajo background programado (tarea Celery)
- Sesiones en estado PAUSADA o ACTIVA existen

### Pasos

1. **Consultar Sesiones Inactivas**
   ```sql
   SELECT * FROM sesiones 
   WHERE estado IN ('ACTIVA', 'PAUSADA')
   AND última_actividad_en < ahora() - INTERVAL '5 minutos'
   AND estado != 'COMPLETADA' AND estado != 'ABANDONADA'
   ```

2. **Para Cada Sesión Inactiva**
   - Verificar: sesión.estado y tiempo desde última_actividad_en
   
   **Si estado = ACTIVA e inactiva > 5 min:**
   ```
   → Sesión.estado = PAUSADA
   → Notificar candidato (correo + dashboard)
   → Mensaje: "Su sesión se pausó por inactividad"
   → Publicar evento: SesiónPausada
   ```
   
   **Si estado = PAUSADA e inactiva > 24 horas:**
   ```
   → Sesión.estado = ABANDONADA
   → Publicar evento: SesiónAbandonada
   → No permitir más reanudación
   → Candidato puede iniciar nueva sesión
   ```

3. **Actualizar Marcas de Tiempo**
   - Sesión.pausada_en o Sesión.abandonada_en = ahora (inmutable)
   - Sesión.última_actividad_en permanece como-está (inmutable)

4. **Publicar Eventos**
   - Evento: **SesiónPausada** o **SesiónAbandonada**
   - Tema: sesión.pausada o sesión.abandonada
   - Carga útil: { id_sesión, id_candidato, estado, pausada_en/abandonada_en }

5. **Limpieza**
   - Si abandonada: limpiar estado sesión Redis (liberar memoria)
   - Marcar sesión para archivado (auditoría solo)
   - Actualizar Candidato.estado si todas sesiones abandonadas (para informes)

### Camino de Éxito
- Sesiones inactivas transicionadas (ACTIVA → PAUSADA → ABANDONADA)
- Candidato notificado
- Eventos publicados

### Caminos de Error

**Error 1: Trabajo Falla**
```
→ Reintentar en próximo ciclo (2 min después)
→ Idempotente (mismo resultado si se ejecuta dos veces)
```

**Error 2: Notificación Falla**
```
→ No bloquear transición sesión
→ Registrar fallo para seguimiento manual
→ Candidato ve cambio estado próximo login
```

### Post-condiciones
- Sesiones inactivas transicionadas (PAUSADA o ABANDONADA)
- Marcas de tiempo inmutables
- Eventos publicados
- Recursos liberados (memoria en Redis)

---

## 📊 Diagrama de Flujo de Eventos

```
Crear Sesión y Consentimiento
        ↓
    [SesiónIniciada]
    [ConsentimientoOtorgado]
        ↓
Intercambio Screening (Bucle)
        ↓
    [MensajeIntercambiado] × N
        ↓
Completar Screening
        ↓
    [ScreeningCompletado]
        ↓
Evaluar Screening
        ↓
    [EvaluaciónCompletada]
        ↓
    (Si recomendación = REVISAR)
        ↓
Cola HITL (Unit 6)
        ↓
    [DecisiónHITLTomada]
        ↓
Detección Inactividad (Background)
        ↓
    [SesiónPausada] → [SesiónAbandonada]
```

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 5 Flujos E2E documentados con pasos, caminos de error, post-condiciones
- [x] Cada flujo incluye transiciones de estado (inmutabilidad cumplida)
- [x] Eventos publicados claramente identificados
- [x] Manejo de errores para red, timeout, fallos lógica negocio
- [x] Pre/post-condiciones para cada flujo
- [x] Todas reglas negocio aplicadas y trazables
- [x] Responsabilidades agregados claras en cada flujo

---

**Generado**: 2026-05-27  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 1 - Flujos E2E (Lógica de Negocio)  
**Estado**: ✅ COMPLETADA
