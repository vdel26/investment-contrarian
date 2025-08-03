# Investment Contrarian Dashboard

A contrarian investment dashboard that aggregates sentiment indicators to provide buy/sell recommendations using CNN Fear & Greed Index, AAII Sentiment Survey, and Bank of America Sell Side Indicator.

## Quick Start

```bash
# Start the dashboard
make run

# Run all tests
make test

# Update market data cache
make update-cache
```

## Email Testing

```bash
# Preview email content
make email-preview

# Send test email
make email-test EMAIL=your@email.com

# Test email service
make email-test-service EMAIL=your@email.com
```

## Environment Variables

```bash
OPENAI_API_KEY     # Required for LLM commentary
SERPAPI_KEY        # Required for SSI data search
RESEND_API_KEY     # Required for email notifications
FROM_EMAIL         # Email sender address
```

## Deployment (Render)

### Quick Deploy
1. Push code to GitHub
2. Connect repository to Render
3. Create Web Service using `render.yaml` configuration
4. Set environment variables in Render dashboard
5. Deploy!

### Environment Variables (Required)
```bash
OPENAI_API_KEY=your_openai_key
SERPAPI_KEY=your_serpapi_key
RESEND_API_KEY=your_resend_key
FROM_EMAIL=your_verified_email@domain.com
DASHBOARD_URL=https://your-app.onrender.com
```

### Services Created
- **Web Service**: Flask dashboard (`app.py`)
- **Cron Job**: Daily data updates (`update_cache.py` at 9 AM UTC)
- **Persistent Disk**: Shared storage for cache files and subscriber data

## Key Files

- `app.py` - Flask web server
- `update_cache.py` - Data refresh script
- `render.yaml` - Render deployment configuration
- `config.py` - Environment configuration
- `CLAUDE.md` - Detailed documentation
- `cache/` - Cached market data
- `email_templates/` - Email templates