# Deployment Guide - Render Platform

## Pre-Deployment Checklist

### 1. Environment Setup
- [ ] All code committed to GitHub repository
- [ ] Environment variables documented in `.env.example`
- [ ] Production configuration tested locally

### 2. API Keys Ready
- [ ] OpenAI API key (for LLM commentary)
- [ ] SerpAPI key (for SSI data search)
- [ ] Resend API key (for email notifications)
- [ ] FROM_EMAIL verified with Resend

## Render Deployment Steps

### 1. Create Render Account
1. Sign up at [render.com](https://render.com)
2. Connect your GitHub account
3. Authorize access to your repository

### 2. Deploy Web Service
1. Click "New" → "Web Service"
2. Select your GitHub repository
3. Configure:
   - **Name**: `investment-contrarian-web`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Starter ($7/month)

### 3. Set Environment Variables
In Render dashboard, add these environment variables:
```
FLASK_ENV=production
OPENAI_API_KEY=your_actual_key
SERPAPI_KEY=your_actual_key
RESEND_API_KEY=your_actual_key
FROM_EMAIL=your_verified_email@domain.com
FROM_NAME=Market Sentiment Terminal
OPENAI_MODEL=gpt-4o
DASHBOARD_URL=https://your-app-name.onrender.com
```

### 4. Add Persistent Disk
1. Go to "Disks" in Render dashboard
2. Create new disk:
   - **Name**: `investment-contrarian-data`
   - **Size**: 1 GB
   - **Mount Path**: `/data`

### 5. Create Cron Job Service
1. Click "New" → "Cron Job"
2. Select your GitHub repository
3. Configure:
   - **Name**: `investment-contrarian-cron`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python update_cache.py`
   - **Schedule**: `0 9 * * *` (9 AM UTC daily)
   - **Plan**: Starter
   - **Environment Variables**: Same as web service
   - **Disk**: Mount same `investment-contrarian-data` disk

## Post-Deployment Verification

### 1. Health Check
Visit: `https://your-app-name.onrender.com/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-03T...",
  "cache_files": {...},
  "subscribers_file": true,
  "environment_configured": true,
  "version": "1.0.0"
}
```

### 2. Test Dashboard
- [ ] Visit main dashboard URL
- [ ] Verify all indicators display correctly
- [ ] Test subscription form

### 3. Test Email System
```bash
# From local machine, test production email
python email_content_generator.py test your@email.com
```

### 4. Verify Cron Job
- [ ] Check Render cron job logs
- [ ] Verify cache files are being updated
- [ ] Check for any errors in scheduled runs

## Monitoring & Maintenance

### Daily Checks
- [ ] Health endpoint responding
- [ ] Cron job completed successfully
- [ ] No errors in application logs

### Weekly Checks
- [ ] Email delivery working
- [ ] Subscriber count growing
- [ ] Data freshness (cache timestamps)

### AAII Data Management
The AAII Excel file needs manual updates:
1. Download `sentiment.xls` from AAII website weekly
2. Upload to production server (method TBD)
3. Or rely on YCharts fallback data

## Troubleshooting

### Common Issues
1. **Environment variables not set**: Check Render dashboard
2. **Disk not mounted**: Verify disk configuration
3. **Cron job failing**: Check logs and file permissions
4. **Email not sending**: Verify Resend API key and FROM_EMAIL

### Render Support
- Documentation: [render.com/docs](https://render.com/docs)
- Support: Available through dashboard
- Community: Discord and forums

## Scaling Considerations

### When to Upgrade
- Traffic > 100 concurrent users → Professional plan
- Need faster builds → Upgrade build minutes
- More storage needed → Increase disk size

### Performance Monitoring
- Use Render's built-in metrics
- Monitor response times via health endpoint
- Track email delivery rates