# GitHub Actions CI/CD Setup

## What Was Created

### Workflow Files
1. **`.github/workflows/e2e-tests.yml`** — Full CI pipeline
   - Multi-browser testing (Chromium, Firefox, WebKit)
   - Comprehensive reporting
   - Test result summaries

2. **`.github/workflows/e2e-ci.yml`** — Simple CI pipeline
   - Quick E2E test runs
   - PR comments with results
   - Artifact uploads

---

## Workflow Features

### e2e-tests.yml (Comprehensive)
```yaml
Triggers:
✅ On push to main/develop
✅ On pull requests
✅ Manual workflow dispatch
✅ Path-based filtering

Tests:
✅ Chromium browser
✅ Firefox browser
✅ WebKit (Safari) browser

Reports:
✅ Playwright HTML reports
✅ Test results (JSON)
✅ Summary in job logs
✅ Artifacts (30-day retention)
```

### e2e-ci.yml (Simple)
```yaml
Triggers:
✅ On push to main/develop/feat/*
✅ On pull requests

Features:
✅ Quick test run (Chromium only)
✅ PR comments with results
✅ HTML report upload
✅ Error handling
```

---

## Setup Instructions

### Step 1: Commit Workflow Files
```bash
cd F:\Private-Runtime-Platform
git add .github/workflows/e2e-*.yml
git commit -m "ci: add E2E test workflows"
git push origin main
```

### Step 2: Verify Workflows (GitHub)
1. Go to: https://github.com/Freshair129/Private-Runtime-Platform/actions
2. Should see:
   - "E2E Tests — Landing Page"
   - "E2E Tests — CI Pipeline"

### Step 3: First Run (Manual Trigger)
1. Go to Actions tab
2. Select "E2E Tests — Landing Page"
3. Click "Run workflow"
4. Wait 15-20 minutes

### Step 4: View Results
1. Check "Artifacts" for:
   - `playwright-report-chromium`
   - `playwright-report-firefox`
   - `playwright-report-webkit`
   - `test-results-json-*`

---

## What Each Workflow Does

### Full Workflow (`e2e-tests.yml`)
**Purpose**: Comprehensive multi-browser testing

```
┌─────────────────────────────────────────┐
│  1. Checkout Code                       │
├─────────────────────────────────────────┤
│  2. Setup Node.js & npm cache          │
├─────────────────────────────────────────┤
│  3. Install Dependencies                │
├─────────────────────────────────────────┤
│  4. Install Playwright & Browsers       │
├─────────────────────────────────────────┤
│  5. Run Tests (Parallel by Browser)     │
│     - Chromium                          │
│     - Firefox                           │
│     - WebKit                            │
├─────────────────────────────────────────┤
│  6. Upload Reports (per browser)        │
├─────────────────────────────────────────┤
│  7. Merge & Publish Results             │
├─────────────────────────────────────────┤
│  8. Generate Summary                    │
└─────────────────────────────────────────┘
```

**Time**: ~15-20 minutes  
**Browsers**: 3 (Chromium, Firefox, WebKit)  
**Artifacts**: 6 uploads

### Simple Workflow (`e2e-ci.yml`)
**Purpose**: Quick feedback on PR/commits

```
┌─────────────────────────────────────────┐
│  1. Checkout                            │
├─────────────────────────────────────────┤
│  2. Setup Node                          │
├─────────────────────────────────────────┤
│  3. Install                             │
├─────────────────────────────────────────┤
│  4. Install Playwright (Chromium)       │
├─────────────────────────────────────────┤
│  5. Run Tests                           │
├─────────────────────────────────────────┤
│  6. Upload Report                       │
├─────────────────────────────────────────┤
│  7. Comment on PR                       │
└─────────────────────────────────────────┘
```

**Time**: ~5-10 minutes  
**Browsers**: 1 (Chromium)  
**Artifacts**: 2 uploads

---

## When Workflows Trigger

### Automatic Triggers
```
┌─────────────────────────┬──────────────────┐
│ Event                   │ Workflow Runs     │
├─────────────────────────┼──────────────────┤
│ Push to main            │ Both              │
│ Push to develop         │ Both              │
│ Push to feat/*          │ CI only           │
│ Pull Request (any)      │ Both              │
│ Create Release          │ —                 │
└─────────────────────────┴──────────────────┘
```

### Automatic (Path-Based Filtering)
Workflows only run if these files changed:
```
e2e/**
package.json
playwright.config.ts
.github/workflows/*
```

---

## GitHub Actions Features

### View Test Results
1. **In GitHub UI**:
   - Actions → Workflow run → Artifacts
   - Download `playwright-report-chromium`

2. **In PR/Commit**:
   - Shows job status ✅/❌
   - Click details for logs
   - PR gets comment with results

### Artifact Retention
```
playwright-report-*   : 30 days
test-results-json-*   : 30 days
merged-playwright-report : 30 days
```

### Job Timeouts
```
Full workflow   : 30 minutes
CI workflow     : 20 minutes
Individual jobs : Auto-scaled
```

---

## Debugging Failed Tests in CI

### 1. Check Logs
```
GitHub → Actions → [Workflow] → Logs
Look for: "Run E2E tests"
```

### 2. Download Report
```
GitHub → Actions → [Workflow] → Artifacts
Download: playwright-report-chromium/
Extract & open: index.html
```

### 3. Check Failed Test Details
In the HTML report:
- Click failed test name
- View screenshot/video
- See error message

### 4. Run Locally to Reproduce
```bash
npm run e2e:headed
# Reproduce the CI failure locally
```

---

## Best Practices

### For Developers
- ✅ Run tests locally before pushing
- ✅ Fix failing tests before PR
- ✅ Review test reports in GitHub
- ✅ Keep tests up-to-date with changes

### For CI Pipeline
- ✅ Keep workflows simple and focused
- ✅ Use path-based filtering
- ✅ Cache dependencies (npm)
- ✅ Use matrix strategy for parallelism
- ✅ Upload artifacts for debugging

### For Maintenance
- ✅ Review workflow logs weekly
- ✅ Archive old artifacts monthly
- ✅ Update node/playwright versions quarterly
- ✅ Add new tests as features are added

---

## Troubleshooting

### Issue: Workflow doesn't run
**Solution**: 
- Check file in `.github/workflows/` is `.yml`
- Verify workflow `on:` triggers
- Check path filtering

### Issue: Tests timeout
**Solution**:
- Increase `timeout-minutes` in workflow
- Check if tests are hanging (browser)
- Run specific test locally with `--debug`

### Issue: Different results locally vs CI
**Solution**:
- CI uses Ubuntu Linux
- Local uses Windows/macOS
- Check browser versions match
- Use `npm ci` (not `npm install`)

### Issue: Artifacts not uploaded
**Solution**:
- Check if job ran successfully
- Verify paths exist in test output
- Check artifact size (<1GB)

---

## Monitoring

### Success Metrics
```
Pass Rate       : 90%+
Test Runtime    : 10-20 min (full) / 5-10 min (CI)
Artifact Size   : <500MB per run
Failed Tests    : <5 per week
```

### When to Alert
- ❌ Pass rate drops below 80%
- ❌ Tests timeout repeatedly
- ❌ Artifacts not uploading
- ❌ Workflow syntax errors

---

## Useful Links

- Workflow Docs: https://docs.github.com/en/actions/using-workflows
- Artifacts: https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts
- Secrets: https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
- Matrix: https://docs.github.com/en/actions/using-workflows/using-a-build-matrix-for-your-jobs

---

## Next Steps

1. ✅ **Commit workflows**: Push `.github/workflows/*.yml`
2. ✅ **Verify**: Check GitHub Actions tab
3. ✅ **Test**: Manual trigger first run
4. ✅ **Fix**: Update workflows if needed
5. ✅ **Automate**: Let it run on every push

---

## Security Notes

- Workflows run in Ubuntu containers (public)
- No secrets in environment by default
- Artifacts accessible to contributors
- Job logs visible in Actions tab

### To Add Secrets (for future)
```
Settings → Secrets → New repository secret
Then use: ${{ secrets.SECRET_NAME }}
```

---

**Ready to deploy CI/CD!**

Next: Commit workflows and push to GitHub
