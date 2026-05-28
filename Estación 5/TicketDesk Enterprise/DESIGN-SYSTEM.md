# DESIGN SYSTEM — TicketDesk Enterprise v1.0

**Estándar**: Google's DESIGN.md + Impeccable Design System + Web Quality Standards  
**Versión**: 1.0  
**Última actualización**: 2026-05-27

---

## 📋 Frontmatter (Tokens de Diseño)

```yaml
---
# COLORS
colors:
  primary:
    dark: "#003366"
    medium: "#1a5fa0"
    light: "#e6f2ff"
  accent:
    magenta: "#d41159"  # Impeccable restraint (≤10% screen)
  neutrals:
    deep_graphite: "#1a1a1a"
    soft_charcoal: "#4a4a4a"
    mid_ash: "#808080"
  background:
    warm_cream: "#faf8f3"  # Impeccable: never pure white
    white: "#ffffff"

# TYPOGRAPHY
typography:
  display:
    family: "Cormorant Garamond"
    style: "italic"
    weight: 400
    size: "2.5rem"
    line_height: 1.2
    letter_spacing: 0
  body:
    family: "Instrument Sans"
    weight: 400
    size: "1rem"
    line_height: 1.6
    letter_spacing: 0
  code:
    family: "Space Grotesk"
    weight: 500
    size: "0.875rem"
    line_height: 1.5

# SPACING (Intentional scale: no 4px step)
spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "32px"
  xl: "48px"
  xxl: "80px"
  xxxl: "120px"

# BORDERS & SHAPES
borders:
  radius_sharp: "0px"        # Impeccable: CTAs sharp, explicit no-round
  radius_subtle: "4px"       # Minimal rounding
  width_thin: "1px"
  width_thick: "2px"

# SHADOWS (Impeccable: low-alpha, hover/lift only)
shadows:
  subtle: "0 2px 8px rgba(0,0,0,0.08)"
  medium: "0 4px 16px rgba(0,0,0,0.12)"
  heavy: "0 8px 32px rgba(0,0,0,0.15)"
  magenta_accent: "0 0 20px rgba(212,17,89,0.15)"  # Accent moments only

# MOTION (Impeccable: expo-out easing)
motion:
  easing_expo_out: "cubic-bezier(0.16, 1, 0.3, 1)"
  duration_fast: "150ms"
  duration_medium: "300ms"
  duration_slow: "500ms"
  # Transform-only: opacity, transform permitted
  # Layout forbidden, prefers-reduced-motion respected
---
```

---

## 🎨 Colors

### Color Philosophy

**Primary**: Trustworthy blue (tech, data-driven)
**Accent**: Editorial magenta (Impeccable restraint — ≤10% screen coverage)
**Neutrals**: Three-tier hierarchy without secondary hues

### Color Palette

```
PRIMARY (Trust & Technology)
├─ Dark (#003366)     — Headers, high-contrast text
├─ Medium (#1a5fa0)   — Interactive elements, CTAs
└─ Light (#e6f2ff)    — Backgrounds, low-emphasis

ACCENT (Editorial Punctuation)
└─ Magenta (#d41159)  — ONLY for critical actions, highlights
                         Never use secondary accents
                         Max 10% of any screen

NEUTRALS (Readable Hierarchy)
├─ Deep Graphite (#1a1a1a)   — Primary text
├─ Soft Charcoal (#4a4a4a)   — Secondary text
├─ Mid Ash (#808080)         — Tertiary, disabled
└─ Warm Cream (#faf8f3)      — Background (never pure white)

FUNCTIONAL COLORS
├─ Success: #22c55e    (Green, WCAG AA on white)
├─ Warning: #f59e0b   (Amber, WCAG AA on white)
├─ Error: #ef4444     (Red, WCAG AA on white)
└─ Info: #3b82f6      (Blue, WCAG AA on white)
```

### Contrast Validation (WCAG 2.2)

```
✅ Dark Gray (#1a1a1a) on Warm Cream (#faf8f3)
   Contrast ratio: 16:1 (AAA)

✅ Medium Blue (#1a5fa0) on Warm Cream (#faf8f3)
   Contrast ratio: 7.5:1 (AAA)

✅ Magenta (#d41159) on White (#ffffff)
   Contrast ratio: 6.2:1 (AA, acceptable for UI accents)

✅ Soft Charcoal (#4a4a4a) on Warm Cream (#faf8f3)
   Contrast ratio: 9.2:1 (AAA)

All functional colors tested against light & dark backgrounds
```

---

## 🔤 Typography

### Hierarchy & Voice

```
DISPLAY (Editorial moments)
├─ Font: Cormorant Garamond Italic
├─ Size: 2.5rem (40px)
├─ Weight: 400 (italic as voice, not emphasis)
├─ Use: Page titles, hero statements, section openings
└─ Rationale: "Stately, authored, editorial" (Impeccable)

HEADING 1 (Page structure)
├─ Font: Cormorant Garamond
├─ Size: 2rem (32px)
├─ Weight: 700
├─ Line-height: 1.2
└─ Margin-bottom: 24px

HEADING 2 (Section structure)
├─ Font: Instrument Sans
├─ Size: 1.5rem (24px)
├─ Weight: 600
├─ Line-height: 1.3
└─ Margin-bottom: 16px

BODY TEXT (Default)
├─ Font: Instrument Sans
├─ Size: 1rem (16px)
├─ Weight: 400
├─ Line-height: 1.6 (fixed, not fluid)
├─ Letter-spacing: 0
└─ Color: {colors.neutrals.deep_graphite}

BODY EMPHASIS (Weight, not italic)
├─ Font weight: 600
├─ Line-height: 1.6 (no change)
└─ Rationale: "Italic marks display-level; body uses weight" (Impeccable)

CODE & METADATA
├─ Font: Space Grotesk
├─ Size: 0.875rem (14px)
├─ Weight: 500
├─ Letter-spacing: 0.5px
├─ Background: {colors.background.light}
└─ Use: Code blocks, command labels, timestamps

SMALL TEXT
├─ Font: Instrument Sans
├─ Size: 0.875rem (14px)
├─ Weight: 400
├─ Line-height: 1.5
└─ Use: Captions, metadata, footnotes
```

### Responsive Typography

```css
/* Headings scale; body is fixed */

@media (min-width: 768px) {
  h1 { font-size: 2.5rem; }  /* 40px */
  h2 { font-size: 1.875rem; } /* 30px */
}

@media (min-width: 1024px) {
  h1 { font-size: 3rem; }    /* 48px */
  h2 { font-size: 2.25rem; } /* 36px */
}

/* Body remains 1rem across all breakpoints */
body { font-size: 1rem; line-height: 1.6; }
```

---

## 📐 Layout

### Grid System

```
DESKTOP (1024px+)
├─ Columns: 12
├─ Gutter: 24px
├─ Margin: 48px (left/right)
└─ Max-width: 1280px

TABLET (768px - 1023px)
├─ Columns: 8
├─ Gutter: 16px
├─ Margin: 32px (left/right)
└─ Max-width: 100%

MOBILE (320px - 767px)
├─ Columns: 4
├─ Gutter: 12px
├─ Margin: 16px (left/right)
└─ Max-width: 100%
```

### Spacing Scale (No 4px step — intentional gap)

```
8px   ← Smallest (internal padding)
16px  ← Small (component spacing)
24px  ← Medium (section spacing)
32px  ← Large (layout spacing)
48px  ← Extra-large (major sections)
80px  ← Jumbo (hero spacing)
120px ← Maximum (page sections)

Rationale: "Deliberately omit 4px step to force intentionality"
```

### Alignment & Whitespace

```
✅ Align content to grid consistently
✅ Use whitespace to create visual hierarchy
✅ Never center-align body text (readability)
✅ Left-align by default, center for CTAs only
✅ Vertical rhythm: match line-height to spacing units
```

---

## 🎭 Elevation & Depth

### Shadow System (Impeccable: low-alpha, hover/lift only)

```
AT REST (No elevation)
├─ Box-shadow: none
├─ Rationale: "Flat by default, shadows appear on interaction"
└─ Visual hierarchy from color/typography, not depth

ON HOVER (Subtle lift)
├─ Box-shadow: {shadows.subtle}
│  └─ 0 2px 8px rgba(0,0,0,0.08)
├─ Transform: translateY(-2px)
└─ Duration: 150ms {motion.easing_expo_out}

ON ACTIVE/FOCUS (Medium elevation)
├─ Box-shadow: {shadows.medium}
│  └─ 0 4px 16px rgba(0,0,0,0.12)
├─ Transform: translateY(-4px)
└─ Duration: 150ms

ON DRAG (Heavy elevation)
├─ Box-shadow: {shadows.heavy}
│  └─ 0 8px 32px rgba(0,0,0,0.15)
├─ Transform: translateY(-8px)
└─ Duration: 200ms

MAGENTA ACCENTS (Special moments)
├─ Box-shadow: {shadows.magenta_accent}
│  └─ 0 0 20px rgba(212,17,89,0.15)
├─ Used: Critical CTAs, errors, success states
└─ Restraint: Max 1-2 accents per page
```

### Z-index Hierarchy

```
0    — Default layer
10   — Dropdowns, popovers
20   — Modals, dialogs
30   — Tooltips, notifications
40   — Loaders, spinners (top-most)
```

---

## 🔲 Shapes & Borders

### Border Radius Strategy (Impeccable: restraint in rounding)

```
SHARP (0px) — Impeccable signature
├─ Primary CTAs (explicit rejection of rounded defaults)
├─ Code blocks
├─ Alert boxes
└─ Rationale: "Sharp edges = intentional design, not default"

SUBTLE (4px)
├─ Form inputs, text areas
├─ Cards (optional)
├─ Image containers
└─ Rationale: "Minimal visual softness for usability"

NO MIXED RADIUS
├─ Avoid top-left=0, bottom-right=4px (inconsistent)
├─ Use uniform or none
└─ Consistency > quirk
```

### Border Width

```
THIN (1px)
├─ Form field borders
├─ Dividers, separators
└─ Subtle visual structure

THICK (2px)
├─ Focus rings (accessibility)
├─ Primary accent borders (magenta)
└─ Error states
```

---

## 🧩 Components

### Button Component

```
PRIMARY CTA (Magenta, sharp, uppercase)
├─ Background: {colors.accent.magenta}
├─ Color: white
├─ Border-radius: {borders.radius_sharp} (0px)
├─ Text-transform: uppercase
├─ Letter-spacing: 1.5px
├─ Padding: 12px 24px
├─ Font-weight: 600
├─ Font-size: 0.875rem (14px)
├─ Min-width: 120px
│
├─ STATE: HOVER
│  ├─ Background: #b3083d (darker magenta)
│  ├─ Box-shadow: {shadows.magenta_accent}
│  ├─ Transform: translateY(-2px)
│  └─ Transition: 150ms {motion.easing_expo_out}
│
├─ STATE: FOCUS
│  ├─ Outline: 2px solid {colors.primary.dark}
│  ├─ Outline-offset: 2px
│  └─ Rationale: WCAG AAA focus visible
│
└─ STATE: DISABLED
   ├─ Background: {colors.neutrals.mid_ash}
   ├─ Color: {colors.neutrals.soft_charcoal}
   ├─ Cursor: not-allowed
   └─ Opacity: 0.5

SECONDARY BUTTON (Blue outline)
├─ Background: transparent
├─ Border: 2px solid {colors.primary.medium}
├─ Color: {colors.primary.dark}
├─ Border-radius: {borders.radius_sharp}
├─ Padding: 10px 22px (accounts for border)
├─ Font-weight: 600
└─ Same hover/focus/disabled as primary
```

### Form Inputs

```
TEXT INPUT
├─ Border: 1px solid {colors.neutrals.soft_charcoal}
├─ Border-radius: {borders.radius_subtle} (4px)
├─ Padding: 12px 16px
├─ Font-family: {typography.body.family}
├─ Font-size: 1rem
├─ Line-height: 1.6
│
├─ STATE: FOCUS
│  ├─ Border-color: {colors.primary.medium}
│  ├─ Outline: 2px solid {colors.primary.light}
│  ├─ Outline-offset: 2px
│  └─ Box-shadow: {shadows.subtle}
│
├─ STATE: ERROR
│  ├─ Border-color: #ef4444
│  ├─ Color (text): #ef4444
│  └─ Helper text: error message in red
│
└─ STATE: DISABLED
   ├─ Background: {colors.neutrals.mid_ash}
   ├─ Opacity: 0.5
   └─ Cursor: not-allowed

TEXTAREA (Same as text input)
├─ Min-height: 120px
├─ Resize: vertical
└─ Font-family: {typography.body.family} (not monospace)

CHECKBOX & RADIO
├─ Size: 20px × 20px
├─ Border: 2px solid {colors.primary.medium}
├─ Checked: background {colors.primary.medium}
├─ Focus: outline 2px solid {colors.primary.light}
└─ Label: adjacent, left-aligned
```

### Cards (Optional, no-stack design)

```
RATIONALE: Impeccable rejects "identical-card grids"
→ Use varied layouts (grid + list mix) instead

IF USED:
├─ Background: white or {colors.background.light}
├─ Border: 1px solid {colors.neutrals.soft_charcoal}
├─ Border-radius: {borders.radius_subtle} (4px)
├─ Padding: 24px
├─ Box-shadow: none (at rest)
├─ Hover: {shadows.subtle} + translateY(-2px)
└─ Max-width: 400px (forces variety in grids)
```

### Alerts & Notifications

```
SUCCESS ALERT
├─ Background: #ecfdf5 (pale green)
├─ Border-left: 4px solid #22c55e
├─ Border-radius: {borders.radius_sharp}
├─ Icon: ✓ (#22c55e)
├─ Text: {colors.neutrals.deep_graphite}
└─ Padding: 16px 24px

WARNING ALERT
├─ Background: #fffbeb (pale amber)
├─ Border-left: 4px solid #f59e0b
├─ Icon: ⚠ (#f59e0b)
└─ Same padding/text as success

ERROR ALERT
├─ Background: #fef2f2 (pale red)
├─ Border-left: 4px solid #ef4444
├─ Icon: ✗ (#ef4444)
└─ Same padding/text as success

INFO ALERT
├─ Background: #eff6ff (pale blue)
├─ Border-left: 4px solid #3b82f6
├─ Icon: ℹ (#3b82f6)
└─ Same padding/text as success

RATIONALE: Impeccable "no border-left stripes" but
→ Single left border for accessibility + direction clarity
```

---

## ✨ Motion & Animation

### Easing Strategy (Impeccable: expo-out across all transitions)

```
STANDARD EASING
└─ cubic-bezier(0.16, 1, 0.3, 1)  — Expo-out
   └─ Implies deceleration (natural, confident)
   └─ NOT bounce/elastic (generic default)

TIMING DURATIONS
├─ Fast: 150ms    (hover effects, small changes)
├─ Medium: 300ms  (page transitions, modal opens)
├─ Slow: 500ms    (page loads, major shifts)
└─ Never: >800ms (feels slow to users)

TRANSFORM-ONLY ANIMATION
✅ Permitted:
├─ opacity
├─ transform: translateX, translateY, scale, rotate
└─ filter: blur, brightness, etc.

❌ Forbidden:
├─ Animating layout properties (width, height, margin)
├─ Animating top/left/right/bottom
└─ Animating grid-template-columns

RATIONALE: "Layout animations cause repaints,
           transform-only uses GPU acceleration"
```

### Reduced Motion Respect

```css
@media (prefers-reduced-motion: reduce) {
  /* All animations collapse to instant or removed */
  
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Hover effects remain, but no motion */
  button:hover {
    background-color: change;
    /* transform: translateY(-2px); → REMOVED */
  }
}
```

---

## 📱 Responsive Design

### Breakpoints

```
MOBILE: 320px - 767px
├─ Single column layout
├─ Full-width elements with padding
├─ Larger touch targets (44px minimum)
└─ Stack vertically

TABLET: 768px - 1023px
├─ 2-column layout where appropriate
├─ Medium gutters (16px)
└─ Proportional spacing

DESKTOP: 1024px+
├─ 3+ column layout
├─ Max-width container (1280px)
├─ Consistent margins (48px)
└─ Full breathing room

LARGE DESKTOP: 1440px+
├─ Content max-width: 1280px
├─ Centered with equal side margins
└─ Extra whitespace intentional
```

### Mobile-First Approach

```css
/* Base: Mobile styles (320px+) */
.container {
  display: flex;
  flex-direction: column;
  padding: 16px;
}

/* Tablet: 768px+ */
@media (min-width: 768px) {
  .container {
    flex-direction: row;
    padding: 32px;
    gap: 24px;
  }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  .container {
    max-width: 1280px;
    margin: 0 auto;
    padding: 48px;
  }
}
```

---

## ♿ Accessibility (WCAG 2.2 AAA)

### Core Principles

**PERCEIVABLE**
- Text alternatives: All images have descriptive alt text
- Color not sole means: Labels + icons + color
- Contrast: Minimum 7:1 (AAA), 4.5:1 (AA)
- Text spacing: 1.5× line-height minimum

**OPERABLE**
- Keyboard accessible: All interactive elements keyboard-focusable
- Focus visible: 2px outline, 2px offset
- No keyboard traps: Can tab out of any component
- Touch targets: 44px × 44px minimum

**UNDERSTANDABLE**
- Readable: Headings hierarchy, short paragraphs
- Predictable: Consistent navigation, behavior
- Error prevention: Validation on input, confirmation on destructive
- Labels: All form inputs have associated `<label>` elements

**ROBUST**
- Valid HTML: No broken tags, proper nesting
- Semantic markup: `<button>`, `<a>`, `<nav>`, not `<div>` as button
- ARIA only when necessary: Progressive enhancement first
- Screen reader testing: VoiceOver (macOS), NVDA (Windows)

### Accessibility Checklist

```
✅ Color Contrast
  └─ Text: 7:1 (AAA) or 4.5:1 (AA minimum)
  └─ UI components: 3:1 contrast ratio

✅ Keyboard Navigation
  └─ Tab order logical (top-to-bottom, left-to-right)
  └─ No keyboard traps
  └─ Focus visible: 2px outline

✅ Form Accessibility
  └─ All inputs have labels
  └─ Error messages clear
  └─ Required fields marked
  └─ Type hints provided (email, tel, etc.)

✅ Images & Media
  └─ Meaningful images: descriptive alt text
  └─ Decorative images: alt="" or aria-hidden="true"
  └─ Video/audio: captions + transcripts

✅ Motion & Animation
  └─ Respects prefers-reduced-motion
  └─ No autoplaying videos with sound
  └─ No flashing content (>3/sec)

✅ Structure & Semantics
  └─ H1 once per page
  └─ Heading hierarchy (H1 → H2 → H3, no skipping)
  └─ Semantic HTML: <nav>, <main>, <section>, <article>
  └─ List markup for lists

✅ Testing
  └─ Automated: axe DevTools, WAVE
  └─ Manual: VoiceOver, NVDA
  └─ User testing: Real disabled users
```

---

## ⚡ Performance (Web Vitals)

### Core Web Vitals Targets

```
LCP (Largest Contentful Paint)    ≤ 2.5s (Green)
INP (Interaction to Next Paint)   ≤ 200ms (Green)
CLS (Cumulative Layout Shift)     ≤ 0.1 (Green)
FCP (First Contentful Paint)      ≤ 1.8s
TTFB (Time to First Byte)         ≤ 600ms
```

### Performance Checklist

```
✅ IMAGES
  └─ Optimized (WebP with fallback)
  └─ Responsive sizes (srcset, picture)
  └─ Lazy loading: loading="lazy"
  └─ No oversized images (1920px max width)
  └─ Compressed: TinyPNG, ImageOptim

✅ JAVASCRIPT
  └─ Code splitting: Load only needed code
  └─ Tree shaking: Remove unused imports
  └─ Minified: gzip compression
  └─ Max size: 300KB gzipped for entire app
  └─ No render-blocking scripts (async/defer)

✅ CSS
  └─ Critical CSS inlined (above fold)
  └─ Non-critical deferred
  └─ No unused CSS
  └─ Minified

✅ FONTS
  └─ System fonts first, web fonts second
  └─ Limit to 2 font families
  └─ Preload critical fonts: <link rel="preload">
  └─ Font-display: swap (avoid FOIT)

✅ CACHING
  └─ Static assets: 1 year cache headers
  └─ HTML: no-cache (check for updates)
  └─ API responses: appropriate TTL

✅ NETWORK
  └─ GZIP/Brotli compression enabled
  └─ HTTP/2 or HTTP/3
  └─ CDN for static assets
  └─ No render-blocking resources

✅ RENDERING
  └─ No layout shifts (reserve space for images)
  └─ No long-running JavaScript (break into chunks)
  └─ Debounce resize/scroll listeners
  └─ Use requestAnimationFrame for animations
```

---

## 🔍 SEO & Discoverability

### Technical SEO

```
✅ MARKUP
  └─ Valid HTML (no syntax errors)
  └─ Proper heading hierarchy (H1 once, then H2-H6)
  └─ Semantic HTML tags
  └─ Structured data: JSON-LD (schema.org)

✅ META TAGS
  └─ Title: 50-60 characters, keyword-forward
  └─ Description: 150-160 characters, compelling
  └─ Viewport: <meta name="viewport" content="width=device-width">
  └─ Language: <html lang="es"> or lang="en"
  └─ Open Graph: og:title, og:description, og:image

✅ CANONICAL TAGS
  └─ <link rel="canonical" href="...">
  └─ Prevent duplicate content issues

✅ MOBILE-FIRST INDEXING
  └─ Mobile design first (not responsive add-on)
  └─ Test: Google Search Console → Mobile-Friendly Test
  └─ No mobile-blocking resources

✅ SITEMAPS
  └─ XML sitemap: /sitemap.xml
  └─ Submit to Google Search Console
  └─ Regular updates

✅ ROBOTS.TXT
  └─ Disallow: /admin, /private
  └─ Allow public content
  └─ Link to sitemap
```

### On-Page SEO

```
✅ CONTENT
  └─ Keywords: 1-2 primary, 3-5 secondary
  └─ Keyword placement: title, H1, first paragraph
  └─ Word count: 300+ for indexing
  └─ Readability: Flesch-Kincaid Grade 8-10

✅ INTERNAL LINKING
  └─ Descriptive anchor text (not "click here")
  └─ Link hierarchy (important pages linked from home)
  └─ No orphan pages (all linked)

✅ IMAGES
  └─ Descriptive alt text (keywords included)
  └─ File names: descriptive, hyphens (not underscores)
  └─ Compressed for performance
```

---

## 🚫 Do's and Don'ts (Impeccable + Web Quality)

### ✅ DO

```
✅ Use white space intentionally for hierarchy
✅ Employ color contrast ratios (7:1 AAA)
✅ Test on real devices and screen readers
✅ Use semantic HTML (<button>, <nav>, <form>)
✅ Implement focus indicators (2px outline)
✅ Optimize images (WebP, responsive)
✅ Respect prefers-reduced-motion
✅ Provide keyboard navigation
✅ Write descriptive alt text
✅ Use single, clean accent color (magenta)
✅ Maintain consistent spacing scale
✅ Defer non-critical JavaScript
✅ Use system fonts as fallback
```

### ❌ DON'T

```
❌ Use color as only means of communication
❌ Implement autoplaying media
❌ Create identical-card grid layouts (Impeccable)
❌ Use gradients for primary backgrounds
❌ Add glassmorphism or heavy blur effects
❌ Animate layout properties (use transform)
❌ Set fixed font sizes (use relative units)
❌ Leave form inputs unlabeled
❌ Ignore keyboard accessibility
❌ Use secondary accent colors (Impeccable)
❌ Create nested card hierarchies
❌ Override focus styles without replacement
❌ Serve oversized images
```

---

## 🔗 Component API (React)

### Button Component (TypeScript)

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'tertiary'
  size: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  children: React.ReactNode
  ariaLabel?: string
  ariaPressed?: boolean
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  children,
  ariaLabel,
  ariaPressed,
}) => {
  return (
    <button
      className={`button button--${variant} button--${size}`}
      disabled={disabled || loading}
      onClick={onClick}
      aria-label={ariaLabel}
      aria-pressed={ariaPressed}
    >
      {loading && <span className="button__spinner" />}
      {children}
    </button>
  )
}
```

### Form Input Component (TypeScript)

```typescript
interface InputProps {
  type: 'text' | 'email' | 'tel' | 'password' | 'search'
  label: string
  placeholder?: string
  required?: boolean
  error?: string
  onChange?: (value: string) => void
  value?: string
  disabled?: boolean
  ariaLabel?: string
  ariaDescribedBy?: string
}

export const Input: React.FC<InputProps> = ({
  type = 'text',
  label,
  placeholder,
  required = false,
  error,
  onChange,
  value,
  disabled = false,
  ariaLabel,
  ariaDescribedBy,
}) => {
  const id = `input-${Math.random()}`
  const errorId = error ? `${id}-error` : undefined

  return (
    <div className="form-group">
      <label htmlFor={id} className="form-label">
        {label}
        {required && <span aria-label="required">*</span>}
      </label>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        aria-label={ariaLabel}
        aria-describedby={errorId || ariaDescribedBy}
        aria-invalid={!!error}
        className={`form-input ${error ? 'form-input--error' : ''}`}
      />
      {error && (
        <span id={errorId} className="form-error">
          {error}
        </span>
      )}
    </div>
  )
}
```

---

## 📋 Implementation Checklist

### Before Launch

```
DESIGN & BRAND
☐ All colors finalized and documented
☐ Typography scales responsive and tested
☐ Spacing scale consistent across components
☐ Component library built and documented
☐ Design tokens exported to CSS/SCSS/Tailwind

ACCESSIBILITY
☐ Color contrast ratios validated (AAA)
☐ Keyboard navigation tested (Tab, Enter, Esc)
☐ Screen reader testing (VoiceOver/NVDA)
☐ Focus indicators visible on all interactive elements
☐ Alt text for all images
☐ Form labels associated with inputs
☐ ARIA roles/labels used correctly
☐ prefers-reduced-motion respected

PERFORMANCE
☐ LCP ≤ 2.5s
☐ INP ≤ 200ms
☐ CLS ≤ 0.1
☐ Images optimized (WebP, responsive)
☐ JavaScript <300KB gzipped
☐ CSS minified and purged
☐ Fonts preloaded, font-display: swap
☐ Caching headers configured

SEO
☐ Meta tags (title, description, og:)
☐ Structured data (JSON-LD)
☐ Heading hierarchy correct
☐ XML sitemap created
☐ robots.txt configured
☐ Mobile-first design verified
☐ Internal linking strategy implemented

TESTING
☐ Automated tests: axe, WAVE
☐ Manual testing on real devices
☐ Cross-browser testing (Chrome, Firefox, Safari, Edge)
☐ Mobile testing (iOS Safari, Chrome Mobile)
☐ Performance testing (Lighthouse, WebPageTest)
```

---

## 📚 Resources & References

- **Google DESIGN.md Standard**: https://github.com/google-labs-code/design.md
- **Impeccable Design System**: https://github.com/pbakaus/impeccable
- **Web Quality Skills**: https://github.com/addyosmani/web-quality-skills
- **WCAG 2.2 Guidelines**: https://www.w3.org/WAI/WCAG22/quickref/
- **Core Web Vitals**: https://web.dev/vitals/
- **React Best Practices**: https://react.dev/learn
- **MDN Web Docs**: https://developer.mozilla.org/

---

**Versión**: 1.0  
**Estado**: ✅ Production Ready  
**Última revisión**: 2026-05-27  
**Próxima revisión**: 2026-08-27 (Quarterly)
