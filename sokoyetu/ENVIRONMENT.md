# Environment Variables and Configuration Guide

This document explains all environment variables used in the SokoYetu system.

## Backend Environment Variables (.env)

Copy `backend/.env.example` to `backend/.env` and configure:

```bash
cd backend
cp .env.example .env
# Edit .env with your actual values
```

### Database Configuration

```
# MySQL (Production - Recommended)
DATABASE_TYPE=mysql
MYSQL_DB=sokoyetu
MYSQL_USER=root
MYSQL_HOST=localhost
MYSQL_PORT=3306
DATABASE_URL=sqlite:///./sokoyetu.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://username:password@localhost:5432/sokoyetu
```

**Notes:**
- SQLite requires no setup, file is created automatically
- PostgreSQL requires pre-created database and user
- Always use environment variables, never hardcode credentials

### JWT Configuration

```
# Secret key for signing JWT tokens
SECRET_KEY=your-very-secret-key-with-32-characters-minimum

# Algorithm for JWT signing
ALGORITHM=HS256

# Token expiration time in minutes
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

**Security:**
- Generate SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Use different SECRET_KEY for each environment (dev/staging/production)
- Never commit .env file to git

### M-Pesa Configuration

```
# Get from Safaricom Daraja Portal (https://sandbox.safaricom.co.ke)
MPESA_CONSUMER_KEY=YOUR_CONSUMER_KEY
MPESA_CONSUMER_SECRET=YOUR_CONSUMER_SECRET
MPESA_SHORTCODE=174379
MPESA_PASSKEY=YOUR_PASSKEY
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback
```

**Setup Steps:**
1. Register at Safaricom Daraja Portal
2. Create an app
3. Get Consumer Key and Consumer Secret
4. Generate STK Push credentials (Shortcode + Passkey)
5. Set Callback URL to your server

**Testing with Sandbox:**
- Use test phone numbers: 254708374149
- Test amount: 1 KES minimum
- STK popups appear on registered test phone

### Email Configuration (SMTP)

```
# Gmail Example
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-specific-password
SMTP_FROM=your-email@gmail.com

# Other providers:
# SendGrid: smtp.sendgrid.net (port 587)
# Mailgun: smtp.mailgun.org (port 587)
# AWS SES: email-smtp.region.amazonaws.com (port 587)
```

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Generate App-Specific Password
3. Use App Password (not regular password) in SMTP_PASS

**Important:** Use app-specific passwords, NOT your actual Gmail password!

### SMS Configuration (Africa's Talking)

```
# Get from https://africastalking.com
AFRICASTALKING_API_KEY=YOUR_API_KEY
AFRICASTALKING_USERNAME=YOUR_USERNAME

# Optional: WhatsApp integration
AFRICATALKING_SHORTCODE=YOUR_SHORTCODE
```

**Setup:**
1. Sign up at Africa's Talking
2. Create an account and generate API key
3. Enable SMS service
4. Set HTTP API endpoint

### File Upload Configuration

```
# Directory for user uploads (photos, receipts)
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=5
ALLOWED_UPLOAD_TYPES=jpg,jpeg,png,pdf
```

### Application Configuration

```
# Server settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true

# CORS settings
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Logging
LOG_LEVEL=info
```

## Frontend Environment Variables (.env.local)

Copy `frontend/.env.example` to `frontend/.env.local`:

```bash
cd frontend
cp .env.example .env.local
# Edit .env.local with your values
```

### API Configuration

```
# Backend API URL
VITE_API_URL=http://localhost:8000

# Request timeout in milliseconds
VITE_API_TIMEOUT=10000
```

### Feature Flags

```
# Enable/disable specific features
VITE_ENABLE_MAPS=true              # Google Maps integration
VITE_ENABLE_GEOFENCING=true        # GPS geofencing
VITE_ENABLE_QR_SCANNER=true        # QR code scanning
VITE_ENABLE_LOCATION_TRACKING=true # Real-time tracking
VITE_ENABLE_NOTIFICATIONS=true     # Push notifications
```

### Application Settings

```
# App metadata
VITE_APP_NAME=SokoYetu
VITE_APP_VERSION=1.0.0

# Google Maps API (if enabled)
VITE_GOOGLE_MAPS_API_KEY=your_api_key_here

# Geolocation
VITE_GEOLOCATION_TIMEOUT=5000      # ms
VITE_GEOLOCATION_MAX_AGE=0         # Fresh location every time
```

## Environment-Specific Configurations

### Development (.env)

```
DATABASE_URL=sqlite:///./sokoyetu.db
SECRET_KEY=dev-secret-key-not-secure
BACKEND_RELOAD=true
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://localhost:8000"]
LOG_LEVEL=debug
```

### Staging (.env.staging)

```
DATABASE_URL=postgresql://user:password@staging-db.example.com/sokoyetu
SECRET_KEY=generate-with-secrets-module
BACKEND_RELOAD=false
CORS_ORIGINS=["https://staging.sokoyetu.com"]
LOG_LEVEL=info
MPESA_SHORTCODE=174379  # Use sandbox
```

### Production (.env.production)

```
DATABASE_URL=postgresql://user:strong_password@prod-db.example.com/sokoyetu
SECRET_KEY=generate-with-secrets-module
BACKEND_RELOAD=false
CORS_ORIGINS=["https://sokoyetu.com","https://app.sokoyetu.com"]
LOG_LEVEL=warning
MPESA_SHORTCODE=YOUR_ACTUAL_SHORTCODE  # Use production code
SMTP_HOST=smtp.sendgrid.net           # Use production email service
```

## Loading Environment Variables

### Python (Backend)

```python
import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

# Access variables
database_url = os.getenv("DATABASE_URL")
secret_key = os.getenv("SECRET_KEY")
```

### JavaScript (Frontend)

```javascript
// Vite automatically loads .env and .env.local
const apiUrl = import.meta.env.VITE_API_URL;
const enableMaps = import.meta.env.VITE_ENABLE_MAPS;
```

## Important Security Notes

### Never in Version Control

These files should NEVER be committed:
- ✅ DO commit: `.env.example` (template only)
- ❌ DON'T commit: `.env` (actual credentials)

Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

### Credential Management

**Development:**
- Use test/sandbox credentials
- Safe to share within team (not in git)
- Use SQLite for simplicity

**Production:**
- Rotate credentials regularly
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Use different credentials per environment
- Enable credential expiration

### Environment Variables in CI/CD

Set environment variables in your CI/CD platform:
- GitHub Actions: Settings → Secrets
- GitLab CI: Settings → CI/CD → Variables
- Circle CI: Project Settings → Environment Variables
- Jenkins: Manage Jenkins → Configure System → Global properties

**Example for GitHub Actions:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: ${{ secrets.DATABASE_URL }}
      SECRET_KEY: ${{ secrets.SECRET_KEY }}
      MPESA_CONSUMER_KEY: ${{ secrets.MPESA_CONSUMER_KEY }}
```

## Configuration Validation

### Backend Configuration Check

```python
# test_config.py
from config import settings

def test_environment_variables():
    assert settings.database_url is not None
    assert settings.secret_key is not None
    assert len(settings.secret_key) >= 32
    assert settings.mpesa_consumer_key is not None
    
print("✅ All required environment variables configured!")
```

Run validation:
```bash
python test_config.py
```

### Frontend Configuration Check

```javascript
// Check that all required env vars are set
const requiredVars = [
  'VITE_API_URL',
  'VITE_APP_NAME'
];

requiredVars.forEach(v => {
  if (!import.meta.env[v]) {
    throw new Error(`Missing required env var: ${v}`);
  }
});

console.log('✅ Frontend configuration valid');
```

## Quick Reference Table

| Variable | Purpose | Example | Required |
|----------|---------|---------|----------|
| DATABASE_URL | Database connection | sqlite:///./sokoyetu.db | ✅ |
| SECRET_KEY | JWT signing key | random-32-char-string | ✅ |
| MPESA_CONSUMER_KEY | M-Pesa API key | YOUR_KEY | ✅ |
| MPESA_CONSUMER_SECRET | M-Pesa API secret | YOUR_SECRET | ✅ |
| SMTP_HOST | Email server | smtp.gmail.com | ✅ |
| SMTP_USER | Email account | email@gmail.com | ✅ |
| AFRICASTALKING_API_KEY | SMS API key | YOUR_KEY | ✅ |
| VITE_API_URL | Backend URL | http://localhost:8000 | ✅ |
| CORS_ORIGINS | Allowed origins | ["http://localhost:5173"] | ⚠️ |
| VITE_GOOGLE_MAPS_API_KEY | Maps API | YOUR_KEY | ❌ |

Legend:
- ✅ Required in all environments
- ⚠️ Configure per environment
- ❌ Optional/feature dependent

## Troubleshooting Configuration Issues

### "Module not found: config"

```bash
# Make sure .env exists
ls backend/.env

# Make sure path is correct
cd backend
python -c "from config import settings; print(settings)"
```

### "Environment variable not found"

```bash
# Set variable manually
export DATABASE_URL="sqlite:///./sokoyetu.db"
python -c "import os; print(os.getenv('DATABASE_URL'))"
```

### "Invalid database URL"

```bash
# Validate database URL
python -c "
from sqlalchemy import create_engine
try:
    engine = create_engine('sqlite:///./sokoyetu.db')
    print('✅ Database connection valid')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## Environment Setup Summary

1. **To get started:**
   ```bash
   cd backend && cp .env.example .env          # Backend
   cd ../frontend && cp .env.example .env.local  # Frontend
   ```

2. **Then configure:**
   - Backend: M-Pesa, Email, SMS, Database
   - Frontend: API_URL, Feature flags

3. **Verify:**
   ```bash
   python test_config.py  # Backend
   npm run dev            # Frontend (checks on startup)
   ```

4. **For production,**
   - Use different .env file
   - Set strong SECRET_KEY
   - Configure real M-Pesa credentials
   - Use PostgreSQL database
   - Enable HTTPS

See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup.
