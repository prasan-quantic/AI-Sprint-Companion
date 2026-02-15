# Render.com Deployment Guide for AI Sprint Companion

**Version:** 1.1.0  
**Date:** February 8, 2026

## Overview

This guide walks you through deploying AI Sprint Companion to Render.com's free tier.

## Prerequisites

1. A GitHub account with this repository pushed
2. A Render.com account (free to create at https://render.com)
3. (Optional) OpenAI API key for real AI functionality
4. (Optional) Jira Cloud account for ticket integration

---

## Deployment Methods

### Method 1: Blueprint Deployment (Recommended)

The easiest way to deploy using the `render.yaml` blueprint file.

#### Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **"New"** → **"Blueprint"**
   - Connect your GitHub account if not already connected
   - Select your repository

3. **Deploy**
   - Render will automatically detect `render.yaml`
   - Review the configuration
   - Click **"Apply"**
   - Wait for deployment (usually 2-5 minutes)

4. **Access Your App**
   - Once deployed, click on the service name
   - Your app URL will be: `https://ai-sprint-companion.onrender.com`

---

### Method 2: Manual Deployment

If you prefer to configure manually through the Render dashboard.

#### Steps:

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **"New"** → **"Web Service"**
   - Connect your GitHub repository

2. **Configure Service**
   | Setting | Value |
   |---------|-------|
   | **Name** | ai-sprint-companion |
   | **Region** | Oregon (US West) |
   | **Branch** | main |
   | **Root Directory** | backend |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | **Plan** | Free |

3. **Add Environment Variables**
   
   Go to **"Environment"** tab and add:
   
   | Key | Value | Notes |
   |-----|-------|-------|
   | `PYTHON_VERSION` | 3.11.0 | Python version |
   | `AI_PROVIDER` | mock | Use `openai` or `azure` for real AI |
   | `OPENAI_API_KEY` | (your key) | Only if using OpenAI |
   | `OPENAI_MODEL` | gpt-4o-mini | Optional |

4. **Deploy**
   - Click **"Create Web Service"**
   - Wait for build and deployment

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | AI backend: `mock`, `openai`, or `azure` | `mock` |

### OpenAI Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | If using OpenAI |
| `OPENAI_MODEL` | Model name | No (default: gpt-4o-mini) |
| `OPENAI_BASE_URL` | Custom API base URL | No |

### Azure OpenAI Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | If using Azure |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | If using Azure |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name | If using Azure |
| `AZURE_OPENAI_API_VERSION` | API version | No (default: 2024-05-01-preview) |

### Jira Integration

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_URL` | Jira instance URL (e.g., https://your-domain.atlassian.net) | If using Jira |
| `JIRA_EMAIL` | Your Jira account email | If using Jira |
| `JIRA_API_TOKEN` | Jira API token | If using Jira |
| `JIRA_PROJECT_KEY` | Project key (e.g., KAN) | If using Jira |

---

## render.yaml Blueprint

The `render.yaml` file in the repository root:

```yaml
services:
  - type: web
    name: ai-sprint-companion
    runtime: python
    region: oregon
    plan: free
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.0"
      - key: AI_PROVIDER
        value: mock
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENAI_MODEL
        value: gpt-4o-mini
      - key: JIRA_URL
        sync: false
      - key: JIRA_EMAIL
        sync: false
      - key: JIRA_API_TOKEN
        sync: false
      - key: JIRA_PROJECT_KEY
        sync: false
```

---

## Post-Deployment Verification

### 1. Health Check

```bash
curl https://ai-sprint-companion.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ai_provider": "mock"
}
```

### 2. Web Interface

Visit: `https://ai-sprint-companion.onrender.com/`

You should see the home page with:
- Navigation bar
- Feature cards (Standup, Stories, Tasks, Jira)
- How It Works section

### 3. API Documentation

Visit: `https://ai-sprint-companion.onrender.com/docs`

You should see the Swagger UI with all endpoints.

---

## Updating the Deployment

### Automatic Updates

If you connected via Blueprint, Render automatically deploys on push to `main`:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

### Manual Redeploy

1. Go to Render Dashboard
2. Select your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## Troubleshooting

### Build Fails

**Issue:** `pip install` fails

**Solution:**
- Check `requirements.txt` exists in `backend/` directory
- Ensure all dependencies are correctly specified
- Check Python version compatibility

### App Crashes on Start

**Issue:** Application exits immediately

**Solution:**
- Check logs in Render dashboard
- Verify environment variables are set
- Ensure `$PORT` is used (not hardcoded port)

### AI Features Not Working

**Issue:** AI returns mock responses when OpenAI expected

**Solution:**
- Verify `AI_PROVIDER` is set to `openai`
- Check `OPENAI_API_KEY` is correctly set (not visible in dashboard for security)
- Test API key is valid

### Jira Integration Not Working

**Issue:** Jira endpoints return "not configured"

**Solution:**
- Verify all four Jira variables are set:
  - `JIRA_URL`
  - `JIRA_EMAIL`
  - `JIRA_API_TOKEN`
  - `JIRA_PROJECT_KEY`
- Test Jira API token is valid
- Check project key exists

---

## Free Tier Limitations

Render.com free tier has some limitations:

| Limitation | Impact |
|------------|--------|
| **Spin Down** | App sleeps after 15 min inactivity |
| **Cold Start** | First request may take 30-60 seconds |
| **Build Minutes** | 500 minutes/month |
| **Bandwidth** | 100 GB/month |

### Mitigating Cold Starts

1. **Health Check Pinger:** Use UptimeRobot or similar to ping `/health` every 14 minutes
2. **Upgrade:** Render's paid plans keep apps running 24/7

---

## Security Best Practices

1. **Never commit API keys** to the repository
2. **Use Render's environment variables** for all secrets
3. **Set `sync: false`** for sensitive variables in render.yaml
4. **Rotate API keys** periodically
5. **Monitor usage** in OpenAI/Jira dashboards

---

## Support

- **Render Documentation:** https://render.com/docs
- **FastAPI Documentation:** https://fastapi.tiangolo.com
- **OpenAI API:** https://platform.openai.com/docs
- **Jira API:** https://developer.atlassian.com/cloud/jira/platform/rest/v3/
