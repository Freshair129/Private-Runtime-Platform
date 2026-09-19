# 🧪 E2E Testing - Quick Start Guide

## What Was Set Up ✅

1. **Playwright Configuration** (`playwright.config.ts`)
   - Multi-browser testing: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
   - Screenshot & video capture on failures
   - HTML, JSON, JUnit report formats

2. **E2E Tests** (`e2e/landing-page.spec.ts`)
   - 35+ test cases
   - Organized in 7 test suites
   - Covers navigation, links, navbar, sitemap, accessibility

3. **npm Scripts** in `package.json`
   ```bash
   npm run e2e              # Run all tests on all browsers
   npm run e2e:landing      # Run only landing page tests
   npm run e2e:headed       # See the browser while tests run
   npm run e2e:debug        # Step through tests manually
   npm run e2e:report       # View results in browser
   ```

---

## Test Suites Covered

### 1️⃣ Navigation & Links
Tests that all section links work:
```
✅ Menu items present
✅ Sticky header navigation
✅ Section anchor links (#approach, #capabilities, etc.)
✅ Scroll-to-section on click
✅ URL hash updates
```

### 2️⃣ Navbar & Menu
Tests navigation bar behavior:
```
✅ Navbar displays all elements
✅ Location selector works
✅ Navbar visibility on scroll
✅ CTA buttons are clickable
✅ Navbar hides/shows correctly
```

### 3️⃣ Sitemap Validation
Tests page structure and links:
```
✅ Page structure is valid
✅ All links have correct hrefs
✅ Meta tags present (charset, viewport)
✅ Semantic HTML is correct
✅ External resources load
```

### 4️⃣ Agent Fleet Chip
Tests floating UI component:
```
✅ Chip displays and animates
✅ Agent roster is visible
✅ Drag-by-header works
✅ localStorage persistence
```

### 5️⃣ Responsive & Performance
Tests on different screen sizes:
```
✅ Mobile (375×667)
✅ Tablet (768×1024)
✅ Desktop
✅ No console errors
✅ Scroll indicator works
```

### 6️⃣ Accessibility
Tests keyboard and screen reader support:
```
✅ Tab navigation works
✅ Focus states visible
✅ Heading hierarchy correct
```

### 7️⃣ System Dock
Tests bottom status dock:
```
✅ Dock displays
✅ Status indicators show
✅ Hides on scroll
```

---

## Running Your First Test

### Option A: Simple run (quiet, pass/fail only)
```bash
npm run e2e:landing
```

### Option B: Watch the browser (headed mode)
```bash
npm run e2e:headed
```

### Option C: Step through manually (debug mode)
```bash
npm run e2e:debug
```

### Option D: View results in browser
```bash
npm run e2e:report
```

---

## What to Fix If Tests Fail

### ❌ Links not found?
- Check the HTML file has `<a href="#section-name">` 
- Verify IDs match: `<div id="section-name">`

### ❌ Menu not detected?
- Verify `.menu-btn` class exists in navbar
- Check CSS classes match test selectors

### ❌ Navigation not working?
- Ensure sticky header `.site-header` uses correct transform/positioning
- Check scroll event listeners are bound

### ❌ Agent chip failing?
- Verify `.agent-chip` class is present
- Check if localStorage is supported in test environment

### ❌ Mobile tests failing?
- Update viewport sizes in test file if device differs
- Check `@media` breakpoints in CSS

---

## Test File Structure

```
e2e/
└── landing-page.spec.ts       # All tests here
    ├── Navigation & Links      # Tests 1-5
    ├── Navbar & Menu           # Tests 6-10
    ├── Sitemap Validation      # Tests 11-15
    ├── Agent Fleet Chip        # Tests 16-19
    ├── Responsive & Performance # Tests 20-24
    ├── Accessibility           # Tests 25-27
    └── System Dock             # Tests 28-35
```

---

## Configuration

### File: `playwright.config.ts`
- **Timeout**: 30 seconds per test
- **Retries**: 0 (on local), 2 (on CI)
- **Browsers**: 5 browsers × 35 tests = 175 total runs
- **Reports**: HTML, JSON, JUnit XML

### File: `./.gitignore` (add these)
```
playwright-report/
test-results/
.playwright/
```

---

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Install Playwright
  run: npx playwright install

- name: Run E2E tests
  run: npm run e2e

- name: Upload report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
    retention-days: 30
```

---

## Expected Test Results

When all tests pass, you should see:
```
✅ 145 tests passed (35 tests × 5 browsers ~ with variants)
⏱️ ~5-10 minutes total runtime
📊 HTML report in playwright-report/index.html
```

---

## Debugging Failed Tests

### View detailed error
```bash
npm run e2e:landing -- --debug
# or
npm run e2e:report
```

### Check specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project="Mobile Chrome"
```

### View video/screenshot
```bash
npm run e2e:report
# Click on failed test → videos/screenshots
```

---

## Performance Expectations

| Metric | Expected |
|--------|----------|
| Total runtime | 5-10 min |
| Per browser | 1-2 min |
| Per test | 10-50 sec |
| Pass rate | >90% |

---

## Next Steps

1. **Run baseline**: `npm run e2e:landing`
2. **Review results**: `npm run e2e:report`
3. **Fix failures**: Update HTML/CSS if needed
4. **Add to CI**: Commit tests to repo
5. **Monitor regressions**: Run before each release

---

## Documentation

- Full guide: `E2E_TESTING.md` ← Read this for detailed info
- This file: `E2E_QUICK_START.md` ← You are here

---

## Support

If tests fail:
1. Check `playwright-report/index.html` for details
2. Run in headed mode: `npm run e2e:headed`
3. Check test selectors against actual HTML
4. Verify CSS classes and IDs match test file

---

**Ready to test?** Run: `npm run e2e:landing`

ยาด้วย! (Good luck!)
