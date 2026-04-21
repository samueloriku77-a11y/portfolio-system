# Deployment & Environment Setup Guide

## Repository Structure

```
sokoyetu/
├── backend/                    # FastAPI backend
│   ├── venv/                  # Virtual environment (git ignored)
│   ├── __init__.py
│   ├── main.py                # FastAPI application
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── auth.py                # JWT authentication
│   ├── config.py              # Environment config
│   ├── database.py            # SQLAlchemy setup
│   ├── requirements.txt        # Python dependencies
│   ├── .env                   # Environment variables (NEVER commit)
│   ├── .env.example           # Template for .env
│   ├── services/
│   │   ├── payment.py
│   │   ├── security.py
│   │   └── notifications.py
│   ├── tests/                 # Test suite
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_payment.py
│   │   ├── test_security.py
│   │   └── test_orders.py
│   └── uploads/               # User uploads (git ignored)
│
├── frontend/                  # React/Vite frontend
│   ├── node_modules/         # Node packages (git ignored)
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── pages/
│   │   ├── components/
│   │   ├── context/
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── .env                  # Frontend environment (git ignored)
│   ├── .env.example          # Template for frontend .env
│   └── .gitignore
│
├── .gitignore                 # Git ignore rules
├── pytest.ini                 # Pytest configuration
├── setup-backend.sh          # Linux/Mac setup script
├── setup-backend.bat         # Windows setup script
├── README.md                 # Main documentation
├── TESTING.md               # Testing guide
└── DEPLOYMENT.md            # This file
```

## .gitignore File

Create/update `.gitignore` to prevent committing sensitive files:

```
# Environment variables
.env
.env.local
.env.*.local

# Virtual environments
venv/
env/
ENV/
.venv/

# Dependencies
node_modules/
__pycache__/
*.pyc
*.egg-info/

# Database
*.db
*.sqlite
*.sqlite3
sokoyetu.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Build outputs
dist/
build/
*.egg

# Uploads
backend/uploads/*
!backend/uploads/.gitkeep

# Coverage
htmlcov/
.coverage
*.cover

# Logs
*.log

# OS
.DS_Store
Thumbs.db
```

## Backend Development Environment

### Environment Variables (.env)

Copy `.env.example` to `.env` and fill in your actual values:

```bash
cd backend
cp .env.example .env
# Edit .env with your credentials
```

**Example .env file:**
```
# Database
DATABASE_URL=sqlite:///./sokoyetu.db
# DATABASE_URL=postgresql://user:password@localhost:5432/sokoyetu

# JWT
SECRET_KEY=your-very-secret-key-DO-NOT-SHARE-IN-PRODUCTION
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# M-Pesa (Get from Safaricom Daraja Portal)
MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback

# Email (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-specific-password

# SMS (Africa's Talking)
AFRICASTALKING_API_KEY=your_key
AFRICASTALKING_USERNAME=your_username

# Files
UPLOAD_DIR=./uploads
```

### Installation Steps

#### Windows (PowerShell)

```powershell
# Navigate to project
cd e:\sokoyetu

# Run setup script
.\setup-backend.bat

# Manually activate if script doesn't
.\venv\Scripts\Activate.ps1

# Verify
python --version
pytest --version
```

#### Linux/Mac (Bash)

```bash
cd /path/to/sokoyetu

# Make script executable
chmod +x setup-backend.sh

# Run setup
./setup-backend.sh

# Verify
python3 --version
pytest --version
```

#### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install pytest pytest-cov

# Setup database
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine); print('✅ Database initialized')"
```

## Frontend Development Environment

### Install Node Packages

```bash
cd frontend

# Copy .env template
cp .env.example .env

# Install dependencies with npm
npm install

# Or use yarn
yarn install
```

### Configure Frontend .env

```
# backend.env.local
VITE_API_URL=http://localhost:8000
VITE_ENABLE_MAPS=true
VITE_ENABLE_QR_SCANNER=true
```

## Running the Application

### Start Backend (Development)

```bash
cd backend

# Activate venv first
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or specify specific settings
uvicorn main:app --reload --host 127.0.0.1 --port 8000 --log-level debug
```

Backend runs on: **http://localhost:8000**
API Docs available at: **http://localhost:8000/docs**

### Start Frontend (Development)

```bash
cd frontend

# Run dev server
npm run dev

# Or with specific port
npm run dev -- --port 3000
```

Frontend runs on: **http://localhost:5173** (or **http://localhost:3000**)

### Running Tests

```bash
cd backend

# Activate venv
source venv/bin/activate

# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test category
pytest tests/test_payment.py -v
```

View coverage report:
```bash
# Windows
start htmlcov/index.html
# Linux/Mac
open htmlcov/index.html
```

## Database Setup

### SQLite (Development)

Uses `sokoyetu.db` automatically. To reset:

```bash
rm backend/sokoyetu.db
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"
```

### PostgreSQL (Production)

Update `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/sokoyetu
```

Install psycopg2:
```bash
pip install psycopg2-binary
```

Create database:
```sql
CREATE DATABASE sokoyetu;
CREATE USER sokoyetu_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE sokoyetu TO sokoyetu_user;
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Update `SECRET_KEY` in `.env` to random value
- [ ] Set `DATABASE_URL` to production Postgres
- [ ] Configure real M-Pesa Daraja credentials
- [ ] Setup SMTP for email notifications
- [ ] Configure Africa's Talking SMS API
- [ ] Enable HTTPS/SSL
- [ ] Set CORS_ORIGINS to your domain
- [ ] Configure logging and error tracking
- [ ] Setup database backups
- [ ] Test all payment flows in production mode

### Backend Deployment

#### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t sokoyetu-backend .
docker run -p 8000:8000 --env-file .env sokoyetu-backend
```

#### Using Gunicorn

```bash
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

#### Using Systemd (Linux)

Create `/etc/systemd/system/sokoyetu.service`:

```ini
[Unit]
Description=SokoYetu Backend API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/sokoyetu/backend
Environment="PATH=/var/www/sokoyetu/venv/bin"
ExecStart=/var/www/sokoyetu/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable sokoyetu
sudo systemctl start sokoyetu
sudo systemctl status sokoyetu
```

### Frontend Deployment

#### Build for Production

```bash
cd frontend
npm run build

# Output in dist/
```

#### Deploy to Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

#### Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

#### Static Server (Apache/Nginx)

**Nginx config:**
```nginx
location / {
    root /var/www/sokoyetu/frontend/dist;
    try_files $uri $uri/ /index.html;
}

location /api {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
}
```

**Apache config:**
```apache
<Directory /var/www/sokoyetu/frontend/dist>
    Options -MultiViews
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^ index.html [QSA,L]
</Directory>

ProxyPass /api http://localhost:8000
```

## Environment Verification

After setup, verify everything works:

### Backend Health Check

```bash
# Check server running
curl http://localhost:8000/api/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "SokoYetu Hyperlocal Delivery API",
#   "version": "1.0.0"
# }
```

### Frontend Health Check

Open browser and visit:
- Frontend: http://localhost:5173 or http://localhost:3000
- API Docs: http://localhost:8000/docs

### Run Tests

```bash
cd backend
pytest -v
# Should show all tests passing
```

## Troubleshooting

### Port Already in Use

```bash
# Windows - Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Database Locked Error

```bash
# Remove old database
rm sokoyetu.db

# Reinitialize
python -c "from database import engine, Base; from models import *; Base.metadata.create_all(bind=engine)"
```

### CORS Errors

Update `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

And ensure backend CORS is configured in `config.py`.

### Module Not Found

```bash
# Ensure virtual environment activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Email Not Sending

Check `.env` has valid SMTP credentials:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-specific-password  # Not your regular password!
```

For Gmail, generate [App Password](https://myaccount.google.com/apppasswords).

## Monitoring & Logs

### Backend Logs

```bash
# In development, logs print to console
# In production, redirect to file:
uvicorn main:app > logs/app.log 2>&1 &
```

### Monitor Database

```bash
# SQLite
sqlite3 sokoyetu.db

# Check tables
.tables

# Query data
SELECT * FROM users LIMIT 5;
```

### Monitor API

Use tools like:
- Postman (testing)
- Sentry (error tracking)
- LogRocket (frontend analytics)
- DataDog (monitoring)

## Security Checklist

- [ ] `SECRET_KEY` is random and long (32+ chars)
- [ ] Database password is strong
- [ ] M-Pesa credentials are not shared
- [ ] HTTPS/SSL enabled in production
- [ ] CORS configured for your domain only
- [ ] Rate limiting enabled on API
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (SQLAlchemy handles this)
- [ ] CSV/serialization injection prevention
- [ ] Regular security updates to dependencies

## Next Steps

1. ✅ Complete backend setup: `./setup-backend.sh` or `.\setup-backend.bat`
2. ✅ Complete frontend setup: `npm install`
3. ✅ Run tests: `pytest -v`
4. ✅ Start both servers
5. ✅ Test manually: Create order → Accept → Deliver
6. ✅ Review security checklist
7. ✅ Deploy to production

See [TESTING.md](TESTING.md) for comprehensive testing guide.
See [README.md](README.md) for project overview and API documentation.
