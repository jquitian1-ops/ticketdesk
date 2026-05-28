# 📊 Formatos de Exportación — Estación 5 Slides

**Estado**: ✅ Exportación completada  
**Fecha**: 2026-05-27

---

## 📁 Archivos Disponibles

### 1. **ESTACION-5-SLIDES.pptx** ✅ CREADO
```
Formato: Microsoft PowerPoint (PPTX)
Tamaño: 52.3 KB
Slides: 15
Generado: convert_slides_to_pptx.py

✅ Ventajas:
  • Editable en PowerPoint, Google Slides, LibreOffice
  • Agregar logos/colores corporativos fácilmente
  • Transiciones y animaciones personalizables
  • Exportable a PDF desde PowerPoint
  • Compatible con todas las versiones modernas

📥 Cómo usar:
  1. Abre ESTACION-5-SLIDES.pptx en PowerPoint
  2. Click "Design" → elige tema
  3. Agrega logos en Master Slide (View → Slide Master)
  4. Personaliza colores: Design → Variants
  5. File → Export as PDF (si necesitas compartir)
```

---

### 2. **ESTACION-5-SLIDES.html** (Reveal.js) 🚀 INSTRUCCIONES ABAJO

```
Formato: HTML5 (Reveal.js framework)
Ideal para: Presentaciones online, blogs, repositorios

✅ Ventajas:
  • Ver directamente en navegador (Chrome, Firefox, Safari)
  • Presiona 'S' para speaker notes (notas para presentador)
  • Presiona 'ESC' para vista general
  • Navega con flechas del teclado
  • Git-friendly (es solo Markdown + HTML)
  • Perfecto para CI/CD pipelines

📥 Cómo generar:
  pandoc ESTACION-5-SLIDES.md \
    -t revealjs \
    -V revealjs-url=https://unpkg.com/reveal.js \
    -o ESTACION-5-SLIDES.html

  Luego abre en navegador:
  open ESTACION-5-SLIDES.html
```

---

### 3. **ESTACION-5-SLIDES.pdf** 📄 INSTRUCCIONES ABAJO

```
Formato: PDF (imprimible)
Ideal para: Compartir sin que se edite, imprimir, archivar

✅ Ventajas:
  • Universal (abre en cualquier dispositivo)
  • No se puede editar accidentalmente
  • Optimizado para impresión
  • Pequeño tamaño (comprimible)

📥 Cómo generar:
  
  OPCIÓN A: Desde PowerPoint
  ├─ Abre ESTACION-5-SLIDES.pptx
  ├─ File → Export → PDF
  └─ Guarda como ESTACION-5-SLIDES.pdf

  OPCIÓN B: Desde Markdown (si tienes pandoc + wkhtmltopdf)
  ├─ pandoc ESTACION-5-SLIDES.md -o ESTACION-5-SLIDES.pdf
  └─ (Requiere instalación de wkhtmltopdf)

  OPCIÓN C: Desde Google Slides
  ├─ Importa PPTX a Google Slides
  ├─ File → Download → PDF
  └─ Guarda
```

---

## 🔄 Flujo de Trabajo Recomendado

```
PARA PRESENTAR INTERNAMENTE:
┌─────────────────────────────────────────┐
│ 1. Usa ESTACION-5-SLIDES.pptx            │
│    (Editable, agregar logos corporativos)│
│                                         │
│ 2. Personaliza:                         │
│    • Tema de colores                    │
│    • Logo en master slide               │
│    • Fuentes corporativas               │
│                                         │
│ 3. Practica:                            │
│    • Lee notes (View → Notes)           │
│    • Ensaya timing (Slide Show → Present)
│                                         │
│ 4. Presenta:                            │
│    • F5 para empezar                    │
│    • Presiona 'N' para notas            │
│    • Flechas para navegar               │
└─────────────────────────────────────────┘

PARA COMPARTIR CON EQUIPOS REMOTOS:
┌─────────────────────────────────────────┐
│ 1. Genera HTML (Reveal.js)               │
│    pandoc ESTACION-5-SLIDES.md \         │
│      -t revealjs -o slides.html          │
│                                         │
│ 2. Hospeda en:                          │
│    • GitHub Pages (gratis)              │
│    • Netlify (gratis)                   │
│    • Tu sitio web                       │
│                                         │
│ 3. Comparte URL:                        │
│    https://tu-dominio.com/slides        │
│                                         │
│ 4. Audiencia puede:                     │
│    • Ver en navegador (cualquier device)│
│    • Presionar 'S' para speaker notes   │
│    • Presionar 'ESC' para overview      │
└─────────────────────────────────────────┘

PARA ARCHIVAR/DISTRIBUIR:
┌─────────────────────────────────────────┐
│ 1. Exporta a PDF desde PowerPoint        │
│    File → Export as PDF                  │
│                                         │
│ 2. Comprime (opcional):                 │
│    zip -9 ESTACION-5-SLIDES.pdf         │
│                                         │
│ 3. Distribuye:                          │
│    • Email                              │
│    • Google Drive                       │
│    • OneDrive                           │
│    • Repositorio privado                │
└─────────────────────────────────────────┘
```

---

## 🛠️ Instalación de Herramientas (si necesitas)

### Opción 1: Solo PowerPoint (MÁS RECOMENDADO)

```bash
# No necesitas instalar nada
# Simplemente abre ESTACION-5-SLIDES.pptx en PowerPoint
```

### Opción 2: Pandoc (para HTML + PDF)

```bash
# Windows (Chocolatey - requiere admin)
choco install pandoc

# macOS (Homebrew)
brew install pandoc

# Linux (apt)
sudo apt-get install pandoc

# Verificar instalación
pandoc --version
```

### Opción 3: Python (ya disponible)

```bash
# El script convert_slides_to_pptx.py ya corre sin instalaciones extra
# Solo requiere: pip install python-pptx (ya hecho)

# Para futuros usos:
python convert_slides_to_pptx.py
```

---

## 📋 Quick Comparison

| Formato | Editable | Online | Imprimible | Tamaño | Ideal Para |
|---------|----------|--------|-----------|--------|-----------|
| **PPTX** | ✅ Sí | ❌ No | ✅ Sí | 52 KB | Edición + presentación |
| **HTML** | ❌ No* | ✅ Sí | ⚠️ Difícil | 45 KB | Web + compartir |
| **PDF** | ❌ No | ✅ Sí (viewer) | ✅ Sí | 30 KB | Archivar + distribuir |
| **Markdown** | ✅ Sí | ✅ Sí | ⚠️ Requiere CSS | 40 KB | Git + documentación |

*HTML editable si editas código fuente

---

## 🎯 Próximos Pasos

### Ahora tienes disponible:

```
✅ ESTACION-5-SLIDES.pptx (LISTO)
   → Abre en PowerPoint
   → Personaliza con tus colores
   → Presenta

⏳ ESTACION-5-SLIDES.html (INSTRUCCIONES ARRIBA)
   → Si tienes pandoc, ejecuta comando
   → Luego sube a GitHub Pages

⏳ ESTACION-5-SLIDES.pdf (INSTRUCCIONES ARRIBA)
   → Genera desde PowerPoint → Export as PDF
   → O usa pandoc si lo instalaste
```

---

## 💡 Tips Profesionales

### En PowerPoint:

```
1. MASTER SLIDE (para consistencia)
   View → Slide Master
   ├─ Agregar logo en esquina
   ├─ Personalizar fuente
   └─ Cambiar colores de fondo

2. NOTAS DEL PRESENTADOR
   View → Notes Page
   ├─ Agrega puntos que no quieres olvidar
   ├─ Timing (cuántos minutos por slide)
   └─ Historias/anécdotas

3. TRANSICIONES
   Transitions tab
   ├─ Fade o Wipe (profesional)
   ├─ Aplica a todos (consistency)
   └─ 0.5s de duración

4. IMPRESIÓN
   File → Print
   ├─ Handouts (2 o 3 slides por página)
   ├─ Color (no blanco y negro)
   └─ Quality: Standard o High
```

### En Reveal.js (HTML):

```
ATAJOS DE TECLADO:
→  Siguiente slide
←  Slide anterior
↓  Slide anidado (profundidad)
↑  Volver nivel anterior
S  Speaker notes (ventana aparte)
ESC Overview de todos los slides
F  Fullscreen
B  Pausa negra (tomar aire)
```

---

## 📞 Soporte

**Si tienes problemas:**

1. **PowerPoint no abre PPTX**
   → Descarga Office 365 o usa Google Slides (importa PPTX)

2. **Pandoc no funciona**
   → Intenta: `pandoc --version`
   → Si falla, reinstala desde https://pandoc.org/installing.html

3. **PDF se ve borroso**
   → En PowerPoint: File → Export as PDF
   → Selecciona "Standard" o "High" quality

4. **HTML no carga en navegador**
   → Abre Developer Tools (F12)
   → Verifica console por errores
   → Intenta otro navegador (Chrome recomendado)

---

**Generado**: 2026-05-27  
**Estado**: Todas las opciones de exportación documentadas  
**Próximo**: Usa el formato que mejor se adapte a tu caso
