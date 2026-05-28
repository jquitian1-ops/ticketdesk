# ♿ Accessibility Guide (WCAG 2.2 AAA)

**Estándar**: WCAG 2.2 Level AAA  
**Audiencia**: Developers, QA, Product Managers  
**Enfoque**: TicketDesk Enterprise — Aplicaciones web interactivas

---

## 🎯 4 Pilares de Accesibilidad

### 1. PERCEIVABLE (Información detectable)

#### Texto Alternativo (Images)

```html
<!-- ✅ BUENO: Descriptivo, contiene contexto -->
<img src="user-avatar.png" alt="User profile photo for Maria Garcia" />

<!-- ❌ MALO: Genérico, no descriptivo -->
<img src="user-avatar.png" alt="image" />

<!-- ❌ MALO: "Image of" es redundante -->
<img src="user-avatar.png" alt="Image of a user avatar" />

<!-- ✅ DECORATIVE: usa alt="" o aria-hidden -->
<img src="divider.png" alt="" aria-hidden="true" />
```

#### Captions & Transcripts

```html
<!-- ✅ VIDEO: Siempre incluir captions -->
<video controls>
  <source src="screening-demo.mp4" type="video/mp4" />
  <track kind="captions" src="screening-demo.vtt" srclang="es" />
</video>

<!-- VTT Format (screening-demo.vtt) -->
WEBVTT

00:00:00.000 --> 00:00:03.000
Bienvenido a la plataforma de screening

00:00:03.000 --> 00:00:07.000
Haz clic en "Nuevo Screening" para comenzar
```

#### Color & Contrast

```
WCAG 2.2 Minimum Contrast Ratios:

Level AA (Standard):
  - Normal text: 4.5:1
  - Large text (18pt+): 3:1

Level AAA (Enhanced):
  - Normal text: 7:1  ← TicketDesk Target
  - Large text (18pt+): 4.5:1

FAIL Examples (< 4.5:1):
  ❌ Light gray on white: #999 on #fff = 2.3:1
  ❌ Medium blue on light blue: #1a5fa0 on #e6f2ff = 3.2:1

PASS Examples (≥ 7:1):
  ✅ Dark gray on white: #1a1a1a on #fff = 16:1
  ✅ Deep blue on cream: #003366 on #faf8f3 = 11.5:1
  ✅ Magenta on white: #d41159 on #fff = 6.2:1

Testing Tools:
  - WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
  - axe DevTools: Browser extension (automated)
  - Chrome DevTools: Built-in (Inspect → Accessibility tab)
```

#### Text Spacing & Readability

```css
/* Minimum spacing requirements (WCAG 2.2 Success Criterion 1.4.12) */

body {
  /* Line height */
  line-height: 1.5;  /* or 150% */
  
  /* Paragraph spacing */
  margin-bottom: 2em;  /* Relates to font-size */
  
  /* Letter spacing */
  letter-spacing: 0.12em;  /* 12% of font-size */
  
  /* Word spacing */
  word-spacing: 0.16em;  /* 16% of font-size */
}

/* Ensure these don't break layout */
@media (prefers-reduced-motion: no-preference) {
  /* Transitions allowed; no conflicts */
}
```

### 2. OPERABLE (Usable con teclado & dispositivos)

#### Keyboard Navigation

```html
<!-- ✅ OPERABLE: Tab order makes sense -->
<form>
  <input type="email" placeholder="Email" />    <!-- Tab 1 -->
  <input type="password" placeholder="Pass" />  <!-- Tab 2 -->
  <button type="submit">Login</button>           <!-- Tab 3 -->
</form>

<!-- ❌ INOPERABLE: No keyboard access (divs as buttons) -->
<div class="button" onclick="doSomething()">
  Click me
</div>

<!-- ✅ FIXED: Semantic button, keyboard support -->
<button onclick="doSomething()">
  Click me
</button>
```

#### Focus Visible

```css
/* ✅ Always provide visible focus indicators */

button:focus,
input:focus,
a:focus {
  outline: 2px solid #003366;          /* Color */
  outline-offset: 2px;                  /* Space from element */
}

/* ✅ Works with :focus-visible (keyboard only) */

button:focus-visible {
  outline: 2px solid #003366;
  outline-offset: 2px;
}

/* ❌ AVOID: Removing focus without replacement */

button:focus {
  outline: none;  /* DON'T DO THIS */
}

/* ✅ If you must customize, provide alternative */

button:focus {
  outline: none;
  box-shadow: 0 0 0 3px #d41159;  /* Magenta halo */
  border-radius: 4px;
}
```

#### No Keyboard Traps

```javascript
// ✅ User can Tab through all elements and escape any
// Modal, dropdown, tooltip, etc. should allow escape

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal()
    setFocus(previouslyFocusedElement)
  }
})

// ❌ BAD: User trapped in autocomplete dropdown
// Cannot Tab out, no Escape handler

// Testing: Tab through entire page, verify no stuck points
```

#### Touch Target Size

```
WCAG 2.2 Minimum Touch Target Size:

44 × 44 CSS pixels (minimum)
└─ Applies to: buttons, links, form inputs, icons

TicketDesk Standard: 48 × 48px (slightly larger)

Spacing between targets: 8px minimum

Example button:
  min-width: 120px
  min-height: 48px
  padding: 12px 24px  ← Ensures 48px height
```

#### No Content Flashing (Seizure Prevention)

```
WCAG 2.2 Criterion 2.3.1: Three Flashes or Below

Prohibited:
  ❌ Content flashing > 3 times per second
  ❌ Large flashes: > 25% of screen area
  ❌ Rapid color changes (high contrast)

Examples to Avoid:
  ❌ Blinking cursors > 3Hz
  ❌ Strobe animations
  ❌ Rapid color transitions

Safe:
  ✅ Animations < 3 Hz
  ✅ Subtle transitions (fade, slide)
  ✅ Limited area flashing
  ✅ Not high contrast
```

### 3. UNDERSTANDABLE (Legible, predecible, ayuda de errores)

#### Language & Readability

```html
<!-- ✅ Page language declared -->
<html lang="es">
  <!-- Content in Spanish -->
</html>

<!-- ✅ language change on specific element -->
<p>
  Welcome to TicketDesk
  <span lang="es">Bienvenido a TicketDesk</span>
</p>

<!-- Content readability -->
<!-- Target: Flesch-Kincaid Grade 8-10 -->
<!-- Readability.com or Hemingway Editor can measure -->

<!-- ✅ Short sentences, clear structure -->
<p>
  TicketDesk is an AI screening platform.
  It helps recruiters evaluate candidates faster.
</p>

<!-- ❌ Complex, hard to read -->
<p>
  TicketDesk, being a sophisticated paradigm of technological advancement,
  endeavors to facilitate the optimization of candidate evaluation processes
  through leveraging artificial intelligence methodologies.
</p>
```

#### Predictable Behavior

```javascript
// ✅ PREDICTABLE: Navigation in same location & behavior
// Sidebar always on left, menu items do same thing

const Navigation = () => (
  <nav aria-label="Main navigation">
    <a href="/home">Home</a>
    <a href="/candidates">Candidates</a>
    <a href="/settings">Settings</a>
  </nav>
)

// ❌ UNPREDICTABLE: Controls change behavior
// Home sometimes on left, sometimes top
// Menu items trigger different actions

// ✅ Consistent behavior: Links open pages, buttons trigger actions
<a href="/page">Link (navigates)</a>
<button onClick={doAction}>Button (action)</button>

// ❌ Confusing: Both look same, different behavior
<div className="link-button" onClick={navigate}>Click me</div>
```

#### Error Prevention & Recovery

```html
<!-- ✅ Form with validation & clear errors -->
<form>
  <div class="form-group">
    <label for="email">Email *</label>
    <input
      id="email"
      type="email"
      required
      aria-required="true"
      aria-describedby="email-error"
    />
    <span id="email-error" class="error" role="alert">
      ❌ Email format invalid (example@domain.com)
    </span>
  </div>

  <button type="submit" disabled={!formValid}>
    Submit
  </button>
</form>

<!-- ✅ Confirmation for destructive actions -->
<dialog id="delete-confirm">
  <p>Are you sure you want to delete this candidate?</p>
  <p>This action cannot be undone.</p>
  <button autofocus>Cancel</button>
  <button onclick="deleteCandidate()">Delete</button>
</dialog>

<!-- ✅ Error messages next to fields -->
<div role="alert" class="form-error">
  Please fix the errors above
</div>
```

### 4. ROBUST (Compatible con assistive tech)

#### Semantic HTML

```html
<!-- ✅ Semantic: Search engine + screen reader friendly -->
<header>
  <h1>TicketDesk</h1>
  <nav aria-label="Main navigation">
    <!-- Links here -->
  </nav>
</header>

<main>
  <article>
    <h2>Candidate Screening</h2>
    <p>Content here...</p>
  </article>
</main>

<footer>
  <p>&copy; 2026 TicketDesk</p>
</footer>

<!-- ❌ Non-semantic: All divs -->
<div class="header">
  <div class="title">TicketDesk</div>
  <div class="nav">
    <!-- Links here -->
  </div>
</div>

<div class="main">
  <div class="article">
    <div class="title">Candidate Screening</div>
    <div>Content here...</div>
  </div>
</div>
```

#### ARIA (When Semantic HTML isn't enough)

```html
<!-- ✅ For accessible name/description -->
<button aria-label="Close notification">×</button>

<!-- ✅ For live regions (updates without page refresh) -->
<div aria-live="polite" aria-atomic="true">
  <!-- Candidate score will update here -->
</div>

<!-- ✅ For expanded/collapsed state -->
<button
  aria-expanded="false"
  aria-controls="panel-1"
  onclick="togglePanel()"
>
  Advanced Filters
</button>
<div id="panel-1" hidden>
  <!-- Filter options -->
</div>

<!-- ✅ For custom widgets with keyboard support -->
<div role="tablist">
  <button role="tab" aria-selected="true">Overview</button>
  <button role="tab" aria-selected="false">Details</button>
</div>

<!-- ❌ AVOID: Using ARIA when semantic HTML exists -->
<div role="button" onclick="submit()">
  Submit  <!-- Wrong: use <button> instead -->
</div>
```

---

## 📋 Testing Checklist

### Automated Testing (First Pass)

```bash
# axe DevTools (Chrome extension)
# Installation: Chrome Web Store → axe DevTools
# Usage: Open DevTools → axe DevTools tab → Scan

# WAVE (WebAIM)
# Installation: Chrome Web Store → WAVE
# Usage: Click WAVE icon → Analyze

# Lighthouse (Built-in)
# Usage: DevTools → Lighthouse → Accessibility score
# Target: 90+ score
```

### Manual Testing

```
KEYBOARD NAVIGATION:
☐ Tab through entire page
☐ Tab order makes sense (left-to-right, top-to-bottom)
☐ Can access all interactive elements
☐ Focus visible at all times
☐ No keyboard traps (can escape modals with Escape)
☐ Can submit forms with Enter

SCREEN READER (VoiceOver - macOS):
☐ Enable: System Preferences → Accessibility → VoiceOver
☐ Cmd+U to open Web Rotor (navigate by type)
☐ Listen for: clear button labels, form instructions, headings
☐ Test with: Safari (best support)

SCREEN READER (NVDA - Windows):
☐ Download: https://www.nvaccess.org/download/
☐ Start Reader, navigate with Arrow keys
☐ Insert key (desktop mode) for NVDA commands
☐ Test: All headings announced, buttons identifiable

CONTRAST CHECKING:
☐ WebAIM Contrast Checker tool
☐ axe DevTools automated checks
☐ Visual inspection (text readable in grayscale)

COLOR BLINDNESS:
☐ Chrome DevTools → Rendering → Emulate vision deficiencies
☐ Test: Deuteranopia, Protanopia, Tritanopia
☐ Ensure color not only means of communication
☐ Add icons/text labels to color-coded elements

MOTION SENSITIVITY:
☐ Check: prefers-reduced-motion respected
☐ Disable animations → page still fully functional
☐ Hover effects still work (visual feedback)
```

### Real User Testing

```
"Nothing About Us Without Us"
→ Test with actual users who have disabilities

Recommended Users:
  - Blind or low vision (screen reader users)
  - Motor impairments (keyboard-only)
  - Deaf or hard of hearing (captions accuracy)
  - Cognitive disabilities (clarity of instructions)

Sample Testing Questions:
  1. Could you navigate the form without a mouse?
  2. Were all interactive elements keyboard-accessible?
  3. Were button purposes clear (from labels + icons)?
  4. Did the page make sense with your screen reader?
  5. Could you understand error messages?
  6. Was animation/motion distracting or necessary?
```

---

## 🔄 Accessible Component Patterns

### Accessible Dropdown Menu

```typescript
// ✅ Semantic, keyboard-accessible, ARIA roles

interface DropdownProps {
  label: string
  items: { id: string; label: string }[]
  onSelect: (id: string) => void
}

export const Dropdown: React.FC<DropdownProps> = ({
  label,
  items,
  onSelect,
}) => {
  const [isOpen, setIsOpen] = React.useState(false)
  const menuRef = React.useRef<HTMLDivElement>(null)
  const [focusIndex, setFocusIndex] = React.useState(0)

  // Close on Escape
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Arrow key navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ') {
        setIsOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setFocusIndex((prev) => (prev + 1) % items.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setFocusIndex((prev) => (prev - 1 + items.length) % items.length)
        break
      case 'Enter':
        e.preventDefault()
        onSelect(items[focusIndex].id)
        setIsOpen(false)
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        break
    }
  }

  return (
    <div ref={menuRef}>
      <button
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={label}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
      >
        {label} {isOpen ? '▲' : '▼'}
      </button>

      {isOpen && (
        <ul
          role="menu"
          aria-label={label}
        >
          {items.map((item, idx) => (
            <li key={item.id} role="none">
              <button
                role="menuitem"
                autoFocus={idx === focusIndex}
                onClick={() => {
                  onSelect(item.id)
                  setIsOpen(false)
                }}
                onKeyDown={handleKeyDown}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

### Accessible Modal Dialog

```typescript
export const Modal: React.FC<{
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}> = ({ isOpen, onClose, title, children }) => {
  const dialogRef = React.useRef<HTMLDialogElement>(null)

  React.useEffect(() => {
    if (isOpen) {
      dialogRef.current?.showModal()
    } else {
      dialogRef.current?.close()
    }
  }, [isOpen])

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
    >
      <div role="document">
        <h1 id="dialog-title">{title}</h1>
        <div id="dialog-description">{children}</div>
        <button
          onClick={onClose}
          aria-label="Close dialog"
        >
          Close
        </button>
      </div>
    </dialog>
  )
}
```

---

## 📚 Resources

- **WCAG 2.2 Guidelines**: https://www.w3.org/WAI/WCAG22/quickref/
- **WebAIM**: https://webaim.org/ (testing guides)
- **MDN Accessibility**: https://developer.mozilla.org/en-US/docs/Web/Accessibility
- **Deque University**: https://dequeuniversity.com/ (free courses)
- **axe DevTools**: https://www.deque.com/axe/devtools/
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/

---

**Versión**: 1.0  
**Estándar**: WCAG 2.2 AAA  
**Target de Cumplimiento**: 100%  
**Próxima revisión**: 2026-08-27
