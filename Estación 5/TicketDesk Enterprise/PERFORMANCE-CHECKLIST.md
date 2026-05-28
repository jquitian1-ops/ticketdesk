# ⚡ Performance Checklist (Core Web Vitals)

**Estándar**: Google Core Web Vitals (2024)  
**Target**: All Green metrics  
**Audiencia**: Developers, DevOps, QA  

---

## 🎯 Core Web Vitals (CWV) — Target Metrics

### 1. LCP (Largest Contentful Paint)

```
METRIC: When the largest content element renders

TARGET: ≤ 2.5 seconds (Green)
  🟢 Good: 0–2.5s
  🟡 Needs improvement: 2.5–4s
  🔴 Poor: > 4s

WHAT COUNTS:
  ✓ Images
  ✓ SVG images
  ✓ Video thumbnail
  ✓ Text blocks (paragraphs, headings)
  ✓ Background images

WHAT DOESN'T COUNT:
  ✗ CSS-only animations
  ✗ Transparent elements
  ✗ Animated inline SVGs

OPTIMIZATION STRATEGIES:
  1. Optimize images (WebP, responsive, lazy-load)
  2. Preload critical resources
  3. Minimize CSS blocking render
  4. Use CDN for static assets
  5. Server-side render or pre-render critical content
  6. Avoid render-blocking scripts
```

### 2. INP (Interaction to Next Paint)

```
METRIC: Responsiveness to user interactions

TARGET: ≤ 200 milliseconds (Green)
  🟢 Good: 0–200ms
  🟡 Needs improvement: 200–500ms
  🔴 Poor: > 500ms

WHAT'S MEASURED:
  ✓ Click / tap
  ✓ Keyboard input
  ✓ Pointer input

OPTIMIZATION STRATEGIES:
  1. Break long tasks into chunks (> 50ms is too long)
  2. Defer non-critical JavaScript
  3. Use requestIdleCallback() for background work
  4. Debounce/throttle event listeners
  5. Use Web Workers for heavy computation
  6. Profile with DevTools Performance tab
```

### 3. CLS (Cumulative Layout Shift)

```
METRIC: Visual stability (no sudden layout shifts)

TARGET: ≤ 0.1 (Green)
  🟢 Good: 0–0.1
  🟡 Needs improvement: 0.1–0.25
  🔴 Poor: > 0.25

WHAT CAUSES SHIFTS:
  ❌ Images without dimensions
  ❌ Ads/embeds loading without space reservation
  ❌ Web fonts causing FOIT/FOUT
  ❌ Dynamic content injection
  ❌ Animation properties (width, height, margin)

OPTIMIZATION STRATEGIES:
  1. Reserve space for images (aspect-ratio CSS)
  2. Avoid inserting content above existing content
  3. Use transform/opacity for animations (not layout props)
  4. Load ads/iframes in containers
  5. Use font-display: swap
  6. Avoid client-side rendered dynamic content
```

### Additional Metrics (Supporting)

```
FCP (First Contentful Paint): ≤ 1.8s
  └─ When first content (text/image) appears

TTFB (Time to First Byte): ≤ 600ms
  └─ Server response time

FID (First Input Delay): Deprecated
  └─ Replaced by INP (more accurate)
```

---

## 📊 Performance Budget

```
RESOURCE BUDGET (TicketDesk):

HTML/CSS:     < 50 KB gzipped   (critical path)
JavaScript:   < 300 KB gzipped  (all JS combined)
Images:       < 500 KB / page   (optimized WebP)
Fonts:        < 100 KB          (2 font families max)
Tracking/3rd: < 50 KB           (minimal, deferred)

TOTAL PAGE:   < 1 MB gzipped    (uncompressed < 3 MB)

PERFORMANCE BUDGET (Network):

Fast 3G:      LCP ≤ 4.5s, TTI ≤ 8s
Fast 4G:      LCP ≤ 2.5s, TTI ≤ 5s (target)
WiFi:         LCP ≤ 1.5s, TTI ≤ 3s
```

---

## ✅ JavaScript Performance

### Code Splitting Strategy

```javascript
// ✅ GOOD: Only load needed code

// Route-based splitting (Next.js)
const CandidateList = dynamic(
  () => import('@/pages/candidates'),
  { loading: () => <Skeleton /> }
)

const EvaluationDetail = dynamic(
  () => import('@/pages/evaluation/[id]'),
  { loading: () => <Skeleton /> }
)

// Component-based splitting
const HeavyChart = dynamic(
  () => import('@/components/chart/AdvancedChart'),
  { loading: () => <div>Loading chart...</div> }
)

// ❌ BAD: Load all code upfront
import * as everything from './pages'  // 500KB bundle
```

### Tree Shaking

```javascript
// ✅ GOOD: Named imports (tree-shakeable)
import { Button, Input } from '@/components/form'

// ❌ BAD: Default import (not tree-shakeable)
import * as FormComponents from '@/components/form'
const { Button, Input } = FormComponents
```

### Minification & Compression

```bash
# Measure before
ls -lh dist/bundle.js
# Output: 850 KB

# Minify (remove whitespace, comments)
npm run build  # Already minifies with bundler

# Compress (GZIP)
# Server should compress automatically
gzip -9 dist/bundle.js  # 850KB → ~250KB

# Brotli (better compression)
brotli dist/bundle.js   # 850KB → ~200KB

# Browser requests with:
# Accept-Encoding: gzip, deflate, br
# Server responds with appropriate encoding
```

### Debounce & Throttle

```typescript
// ❌ BAD: Fires 100+ times per second
window.addEventListener('resize', () => {
  recalculateLayout()  // Expensive operation
})

// ✅ GOOD: Debounce (waits until stops)
const debouncedResize = debounce(() => {
  recalculateLayout()
}, 300)
window.addEventListener('resize', debouncedResize)

// Debounce implementation
function debounce<T extends (...args: any[]) => void>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

// ✅ GOOD: Throttle (max once per interval)
const throttledScroll = throttle(() => {
  checkPosition()  // Fires max 60/sec
}, 16)  // ~60fps
window.addEventListener('scroll', throttledScroll)
```

### Web Workers (Offload heavy work)

```javascript
// Main thread (UI-safe)
const worker = new Worker('/workers/calculation.js')

worker.postMessage({
  type: 'CALCULATE_SCORES',
  data: candidateResponses,
})

worker.onmessage = (event) => {
  const scores = event.data
  updateUI(scores)  // Non-blocking
}

// calculation.js (Worker thread)
self.onmessage = (event) => {
  if (event.data.type === 'CALCULATE_SCORES') {
    const result = expensiveCalculation(event.data.data)
    self.postMessage(result)  // Send back to main
  }
}

// Benefit: 0 impact on main thread → smooth UI
```

---

## 🖼️ Image Performance

### Responsive Images

```html
<!-- ✅ GOOD: Multiple sizes, format negotiation -->

<picture>
  <!-- Modern browsers: WebP -->
  <source srcset="/candidates-800w.webp 800w,
                   /candidates-1200w.webp 1200w"
          type="image/webp" />
  
  <!-- Fallback: JPEG -->
  <source srcset="/candidates-800w.jpg 800w,
                   /candidates-1200w.jpg 1200w"
          type="image/jpeg" />
  
  <!-- Oldest browsers: single JPEG -->
  <img src="/candidates-800w.jpg"
       alt="Candidate screening dashboard"
       width="800"
       height="600" />
</picture>

<!-- ❌ BAD: Single large image -->
<img src="/candidates-full-hd.jpg" alt="..." />
```

### Image Optimization

```bash
# Convert to WebP (30-35% smaller)
cwebp -q 80 candidates.jpg -o candidates.webp

# Compress JPEG
jpegoptim -m85 --all-progressive candidates.jpg

# Compress PNG
optipng -o2 candidates.png

# Responsive image generation
# Use sharp library (Node.js)
const sharp = require('sharp')

sharp('candidates.jpg')
  .resize(800, 600)
  .webp({ quality: 80 })
  .toFile('candidates-800w.webp')

sharp('candidates.jpg')
  .resize(1200, 900)
  .webp({ quality: 80 })
  .toFile('candidates-1200w.webp')
```

### Lazy Loading

```html
<!-- ✅ Native lazy loading -->
<img src="candidate.jpg"
     alt="Candidate"
     loading="lazy"
     width="200"
     height="200" />

<!-- ✅ Also works with iframes -->
<iframe src="/video-reviews"
        loading="lazy"></iframe>

<!-- ✅ With width/height (prevents layout shift) -->
<img src="candidate.jpg"
     alt="Candidate"
     loading="lazy"
     width="200"
     height="200"
     style="aspect-ratio: 1" />
```

### Image Format Selection

```
WebP:      Best format (85% modern browser support)
           └─ 30-35% smaller than JPEG

AVIF:      Next-gen (newer browsers)
           └─ 50-60% smaller than JPEG
           └─ Safari/older Firefox: no support yet

JPEG:      Fallback (universal support)
           └─ Progressive JPEG for better perceived performance

PNG:       For graphics, transparency
           └─ Larger than JPEG (avoid for photos)

SVG:       Vector graphics, icons
           └─ Infinitely scalable
           └─ Text-based (cacheable)
```

---

## 📝 CSS Performance

### Critical CSS

```html
<!-- ✅ GOOD: Critical CSS inlined, rest deferred -->

<style>
  /* Critical: Above-the-fold styles */
  body { font-family: sans-serif; }
  header { background: #003366; }
  h1 { color: white; }
  button { padding: 12px 24px; }
</style>

<!-- Deferred non-critical CSS -->
<link rel="preload" href="/styles/non-critical.css" as="style" />
<link rel="stylesheet" href="/styles/non-critical.css" media="print" onload="this.media='all'" />

<!-- ❌ BAD: Inline all CSS -->
<style>
  /* 500KB of CSS inlined */
</style>

<!-- ❌ BAD: Render-blocking stylesheet -->
<link rel="stylesheet" href="/styles/all.css" />
```

### CSS Minification & Purging

```bash
# Minify CSS
npm install -D cssnano
npx cssnano input.css > output.min.css

# Purge unused CSS (Tailwind, PostCSS)
npm install -D purgecss
purgecss --css input.css --content index.html --output output.css

# Check CSS size before/after
ls -lh styles.css      # 150 KB
ls -lh styles.min.css  # 42 KB (72% reduction)
```

---

## 🔤 Font Performance

### Font Loading Strategy

```html
<!-- ✅ GOOD: Preload critical fonts -->

<!-- Preload WOFF2 (modern, smallest) -->
<link rel="preload"
      href="/fonts/instrument-sans-400.woff2"
      as="font"
      type="font/woff2"
      crossorigin />

<!-- Specify font-display strategy -->
<style>
  @font-face {
    font-family: 'Instrument Sans'
    src: url('/fonts/instrument-sans-400.woff2')
    font-display: swap  /* Show fallback immediately */
  }
</style>

<!-- Fallback: System fonts -->
body {
  font-family: 'Instrument Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
}

<!-- ❌ BAD: Multiple font files, no preload -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Cormorant+Garamond|Instrument+Sans" />
```

### Font Optimization

```
Font file sizes:
  TTF:   ~100 KB
  OTF:   ~100 KB
  WOFF:  ~70 KB (30% smaller)
  WOFF2: ~50 KB (50% smaller) ← Best

Font strategies:
  font-display: auto     ← Default (block 3s, then swap)
  font-display: block    ← Hide until loaded (avoid)
  font-display: swap     ← Show fallback immediately ✅
  font-display: fallback ← Short block, fast swap
  font-display: optional ← May not load if slow

Recommended: font-display: swap
→ Show system font immediately, swap when loaded
```

---

## 🗄️ Caching Strategy

### HTTP Caching Headers

```
# Static assets (images, CSS, JS)
Cache-Control: public, max-age=31536000, immutable
└─ 1 year cache (must have hash in filename)

# HTML (never cache)
Cache-Control: public, max-age=0, must-revalidate
└─ Check for updates on every request

# API responses (15 minutes)
Cache-Control: public, max-age=900
└─ Fresh for 15 min, then revalidate

# Service Worker (24 hours)
Cache-Control: public, max-age=86400
└─ Cache for 1 day
```

### Asset Versioning

```
✅ Good: Hash in filename
  /js/app-a1b2c3d4.js    ← Hash changes when file changes
  /css/styles-f5e6d7c8.css

✅ Good: CDN cache busting
  /js/app.js?v=1.0.0     ← Version query string

❌ Bad: No versioning
  /js/app.js             ← Always requests (no cache benefit)
```

---

## 🚀 Server Optimization

### Server Response Time (TTFB ≤ 600ms)

```
Network latency: ~100ms (fixed)
Server processing: Target ≤ 500ms
└─ Database queries ≤ 100ms
└─ Rendering/template ≤ 300ms
└─ Cache lookup ≤ 50ms

Strategies:
  1. Database query optimization (indexes, caching)
  2. Use CDN (reduces latency by 50-70%)
  3. Enable compression (gzip/brotli)
  4. Use Edge caching (CloudFlare, Vercel)
  5. Serve from closest region
```

### API Response Optimization

```typescript
// ✅ GOOD: Only send needed data
app.get('/api/candidates', (req, res) => {
  const candidates = db.query(`
    SELECT id, name, email, score FROM candidates
    WHERE status = 'pending'
    LIMIT 20
  `)
  res.json(candidates)  // 10 KB response
})

// ❌ BAD: Send all data including everything
app.get('/api/candidates', (req, res) => {
  const candidates = db.query('SELECT * FROM candidates')
  res.json(candidates)  // 500 KB response (50x larger)
})

// ✅ GOOD: Pagination
app.get('/api/candidates?page=1&limit=20', (req, res) => {
  const offset = (req.query.page - 1) * req.query.limit
  const candidates = db.query(`
    SELECT id, name, email, score FROM candidates
    LIMIT ${req.query.limit} OFFSET ${offset}
  `)
  res.json(candidates)
})
```

---

## 📋 Performance Testing Checklist

### Automated Testing

```bash
# Lighthouse (Chrome DevTools)
# Usage: DevTools → Lighthouse tab → Analyze page load
# Targets: 90+ performance score

# WebPageTest (https://webpagetest.org/)
# Free tool for detailed waterfall charts
# See: request by request, identify bottlenecks

# Speedcurve (https://www.speedcurve.com/)
# Continuous monitoring, trend detection

# Sentry Performance
# Real user monitoring (RUM)
# Track actual user metrics vs lab metrics
```

### Manual Testing

```bash
# Chrome DevTools Performance tab
# 1. Open DevTools → Performance
# 2. Record (⚫ button)
# 3. Interact with page
# 4. Stop recording
# 5. Analyze flame chart
# Look for: Long tasks, layout thrashing, forced reflows

# Network tab
# 1. Open DevTools → Network
# 2. Reload page
# 3. Check: Request sizes, waterfall, timing
# Targets:
#   - Total size < 1 MB
#   - CSS/JS < 300 KB
#   - Images optimized

# Rendering tab
# 1. DevTools → More tools → Rendering
# 2. Enable "Paint flashing"
# 3. Interact with page
# 4. Look for: Unnecessary repaints, layout thrashing

# Sensors tab (mobile simulation)
# 1. DevTools → More tools → Sensors
# 2. Network throttling: Fast 3G
# 3. CPU throttling: 6x slowdown
# 4. Test on real conditions
```

### Real User Monitoring (RUM)

```javascript
// ✅ Track real user metrics

// Core Web Vitals
const webVitalsMetrics = {
  LCP: null,  // Largest Contentful Paint
  INP: null,  // Interaction to Next Paint
  CLS: null,  // Cumulative Layout Shift
}

// Web Vitals library (Google)
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

getLCP((metric) => {
  console.log('LCP:', metric.value)
  // Send to analytics
  sendToAnalytics(metric)
})

getINP((metric) => {
  console.log('INP:', metric.value)
  sendToAnalytics(metric)
})

getCLS((metric) => {
  console.log('CLS:', metric.value)
  sendToAnalytics(metric)
})

// Send to Sentry, DataDog, or custom analytics
function sendToAnalytics(metric) {
  navigator.sendBeacon('/api/metrics', JSON.stringify(metric))
}
```

---

## 🎯 Performance Goals & Budgets

```
TICKETDESK TARGETS:

Frontend:
  LCP: 2.5s or less (Green)
  INP: 200ms or less (Green)
  CLS: 0.1 or less (Green)
  Bundle size: 300 KB JS (gzipped)
  Total page: < 1 MB (optimized)
  Lighthouse score: 90+

Backend:
  API TTFB: ≤ 600ms
  P95 latency: ≤ 200ms
  Database queries: ≤ 100ms average
  Cache hit rate: > 85%

Infrastructure:
  CDN coverage: Global
  Edge caching: Enabled
  Compression: Brotli 11
  HTTP/3: Enabled
```

---

## 📚 Resources

- **Google Web Vitals**: https://web.dev/vitals/
- **Lighthouse**: https://developers.google.com/web/tools/lighthouse
- **WebPageTest**: https://www.webpagetest.org/
- **Web Almanac**: https://almanac.httparchive.org/
- **Speedcurve**: https://www.speedcurve.com/
- **Sentry Performance**: https://sentry.io/for/performance/

---

**Versión**: 1.0  
**Estándar**: Google Core Web Vitals 2024  
**Target Performance**: 90+ Lighthouse Score  
**Próxima revisión**: 2026-08-27
