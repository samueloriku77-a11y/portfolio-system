import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file (located in parent directory)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Database Configuration
# Supports SQLite (default), PostgreSQL, and MySQL

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")

if DATABASE_URL:
    if "sqlite" in DATABASE_URL:
        DATABASE_TYPE = "sqlite"
    else:
        DATABASE_TYPE = "mysql"  # Default to pool config for anything not sqlite

if not DATABASE_URL:
    if os.getenv("VERCEL"):
        raise RuntimeError(
            "CRITICAL ERROR: No DATABASE_URL found in Vercel Environment Variables. "
            "Please add the Aiven MySQL database link in Vercel Settings -> Environment Variables."
        )

    # SQLite (Default - no setup needed)
    if DATABASE_TYPE == "sqlite":
        DATABASE_URL = "sqlite:///./sokoyetu.db"

    # PostgreSQL
    elif DATABASE_TYPE == "postgresql":
        PG_USER = os.getenv("POSTGRES_USER", "postgres")
        PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
        PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
        PG_PORT = os.getenv("POSTGRES_PORT", "5432")
        PG_DB = os.getenv("POSTGRES_DB", "sokoyetu")
        
        if PG_PASSWORD:
            DATABASE_URL = f"postgresql://{PG_USER}:{quote_plus(PG_PASSWORD)}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        else:
            DATABASE_URL = f"postgresql://{PG_USER}@{PG_HOST}:{PG_PORT}/{PG_DB}"

    # MySQL
    elif DATABASE_TYPE == "mysql":
        MYSQL_USER = os.getenv("MYSQL_USER", "root")
        MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
        MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
        MYSQL_DB = os.getenv("MYSQL_DB", "sokoyetu")
        
        if MYSQL_PASSWORD:
            DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        else:
            DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "sokoyetu-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# M-Pesa Configuration (Daraja API)
# Fill in real credentials for production
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "sandbox_key")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "sandbox_secret")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY", "sandbox_passkey")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL", "https://yourdomain.com/api/mpesa/callback")

# IntaSend Configuration (Mobile money payments)
INTASEND_API_URL = os.getenv("INTASEND_API_URL", "https://sandbox.intasend.co/v1")
INTASEND_API_KEY = os.getenv("INTASEND_API_KEY", "")
INTASEND_API_SECRET = os.getenv("INTASEND_API_SECRET", "")
INTASEND_CALLBACK_URL = os.getenv("INTASEND_CALLBACK_URL", "https://yourdomain.com/api/wallet/callback")

# Notifications Configuration
# Africa's Talking (SMS)
AFRICASTALKING_API_KEY = os.getenv("AFRICASTALKING_API_KEY", "sandbox")
AFRICASTALKING_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "sandbox")

# Email (Gmail SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "your@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "your_app_password")

# File Uploads (Vercel uses read-only filesystem, must use /tmp)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/uploads" if os.getenv("VERCEL") else "./uploads")
