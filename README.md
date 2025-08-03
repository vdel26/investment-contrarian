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

## Key Files

- `app.py` - Flask web server
- `update_cache.py` - Data refresh script
- `CLAUDE.md` - Detailed documentation
- `cache/` - Cached market data
- `email_templates/` - Email templates