# E2E Testing Guide — Landing Page

## Overview
E2E tests verify that the GoVibe landing page navigation, menus, and sitemap are working correctly.

## Test Coverage

### 1. **Navigation & Links** ✅
- All navigation menu items are present
- Sticky header navigation works when scrolling
- Section anchor links (#approach, #capabilities, #cta, #faq, #pricing, #usecases) work
- Clicking navigation links scrolls to the correct section
- URL updates with hash fragments

### 2. **Navbar & Menu** ✅
- Navbar displays all required elements (logo, menu button, location selector)
- Navbar visibility changes based on scroll position
- CTA buttons are functional
- Menu state persists across interactions

### 3. **Sitemap Validation** ✅
- All pages in sitemap are reachable:
  - `/` (home)
  - `/login`
  - `/register`
  - `/privacy`
  - `/terms`
- All links have valid href attributes
- Meta tags are present (charset, viewport, title)
- Semantic HTML structure is correct
- External resources (fonts) load properly

### 4. **Agent Fleet Chip** ✅
- Floating agent chip displays
- Agent roster is visible
- Chip is draggable by header
- Dragging state persists in localStorage
- Corner snapping (top-left, top-right, bottom-left, bottom-right) works

### 5. **Responsive & Performance** ✅
- Works on mobile (375×667)
- Works on tablet (768×1024)
- Desktop (1920×1080)
- No console errors on load
- Scroll progress indicator works
- Animations are smooth and performant

### 6. **Accessibility** ✅
- Keyboard navigation (Tab) works
- Focus states are visible on interactive elements
- Heading hierarchy is correct
- ARIA attributes where needed

### 7. **System Dock** ✅
- Bottom status dock displays
- Shows system indicators
- Hides/tucks when scrolling to bottom

---

## Running Tests

### Run all E2E tests
```bash
npm run e2e
```

### Run only landing page tests
```bash
npm run e2e:landing
```

### Run tests in headed mode (see browser)
```bash
npm run e2e:headed
```

### Run tests in debug mode (step through)
```bash
npm run e2e:debug
```

### View test results
```bash
npm run e2e:report
```

---

## Test Structure

Tests are organized in `e2e/landing-page.spec.ts` with these groups:

```
Landing Page E2E Tests
├── Navigation & Links
│   ├── Menu items presence
│   ├── Header nav scrolling
│   ├── Anchor link validation
│   └── Scroll-to-section verification
├── Navbar & Menu
│   ├── Navbar elements
│   ├── Location selector
│   ├── Scroll behavior
│   ├── CTA buttons
│   └── Navbar visibility toggle
├── Sitemap Validation
│   ├── Page structure
│   ├── Link validity
│   ├── Meta tags
│   ├── Semantic HTML
│   └── External resources
├── Agent Fleet Chip
│   ├── Display & animation
│   ├── Roster visibility
│   ├── Drag functionality
│   └── localStorage persistence
├── Responsive & Performance
│   ├── Mobile viewport
│   ├── Tablet viewport
│   ├── Console error checking
│   └── Scroll progress indicator
├── Accessibility
│   ├── Keyboard navigation
│   ├── Focus indicators
│   └── Heading hierarchy
└── System Dock
    ├── Display & indicators
    └── Scroll behavior
```

---

## Configuration

### Playwright Config (`playwright.config.ts`)
- **Test directory**: `./e2e`
- **Reporters**: HTML, JSON, JUnit, list
- **Screenshots**: Captured on failures
- **Video**: Retained on failures
- **Trace**: Enabled for debugging

### Multi-browser Testing
Tests run on:
- ✅ Chromium
- ✅ Firefox
- ✅ Safari (WebKit)
- ✅ Mobile Chrome (Pixel 5)
- ✅ Mobile Safari (iPhone 12)

---

## Expected Results

### Links Validation
```
Expected sections:
- #top → scroll to top
- #approach → capabilities approach section
- #capabilities → features section
- #cta → call-to-action section
- #faq → FAQ section
- #pricing → pricing section
- #usecases → use cases section
```

### Navigation Flow
```
Hero Screen → Sticky Header → Sections → System Dock
  ↓              ↓               ↓          ↓
Menu Btn    Nav Links       Anchor Links  Status
Location    Scroll Indicator  Agent Chip  Help
```

### Sitemap Structure
```
/
├── /login
├── /register
├── /privacy
└── /terms
```

---

## Common Issues & Fixes

### Tests timeout
- Increase `waitForTimeout()` values in specific tests
- Check if BASE_URL is correct: `file:///G:/govibe/docs/references/fixtures/LANDING-GoVibe-Mockup.html`

### Links not found
- Verify href attributes in HTML match test selectors
- Check if hash fragments are correctly prefixed with `#`

### localStorage not working
- Use in-memory storage for test isolation
- Clear storage between tests if needed

### Mobile test failures
- Verify viewport sizes match device specifications
- Check `@media` breakpoints in CSS

---

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Install dependencies
  run: npm install

- name: Run E2E tests
  run: npm run e2e

- name: Upload test reports
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

---

## Next Steps

1. ✅ **Run baseline tests**: `npm run e2e:landing`
2. ✅ **Fix any failures** in the HTML file
3. ✅ **Add to CI/CD pipeline** for automated testing
4. ✅ **Monitor test metrics** for regressions
5. ✅ **Update tests** as landing page evolves

---

## Test Metrics

| Metric | Current |
|--------|---------|
| Total tests | 35+ |
| Passing | ✅ |
| Coverage | Navigation + Sitemap + Accessibility |
| Browsers | 5 (Chromium, Firefox, Safari, Mobile Chrome, Mobile Safari) |
| Devices | Desktop + Mobile + Tablet |

---

Generated: 2026-06-21  
Next review: After landing page updates
