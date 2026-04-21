# SokoYetu Quick Start - MySQL + Login Fix

## ⚠️ Login Issue Fixed!

The login was failing because the response wasn't properly serializing the User object. This is now **FIXED** in:
- `/api/auth/login` - Now converts User to UserOut schema
- `/api/auth/register` - Now converts User to UserOut schema

## 🚀 Quick Setup (5 Minutes)

### 1. Start MySQL in XAMPP
- Open XAMPP Control Panel
- Click **Start** next to MySQL
- Wait for green "Running" status

### 2. Import Database
- Click **Admin** next to MySQL (opens phpMyAdmin)
- Click **Import** tab
- Choose file: `sokoyetu_mysql.sql` (in project root)
- Click **Go**
- Wait for "Import successful" message

### 3. Start Backend
```
cd e:\sokoyetu\backend
python main.py
```

Should show:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4. Test Login

**Using curl:**
```
curl -X POST http://localhost:8000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"customer1@test.com\",\"password\":\"password123\"}"
```

**Expected response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "customer1@test.com",
    "name": "John Customer",
    "role": "CUSTOMER",
    "phone": "+254700000001",
    "wallet_balance": 5000.0,
    ...
  }
}
```

## 📝 Available Test Users

```
Email: customer1@test.com     | Role: CUSTOMER | Balance: 5000 KES
Email: customer2@test.com     | Role: CUSTOMER | Balance: 2000 KES
Email: vendor1@test.com       | Role: VENDOR   | Balance: 0 KES
Email: vendor2@test.com       | Role: VENDOR   | Balance: 0 KES
Email: driver1@test.com       | Role: DRIVER   | Balance: 0 KES
Email: driver2@test.com       | Role: DRIVER   | Balance: 1500 KES
Email: admin@test.com         | Role: ADMIN    | Balance: 0 KES
```

**All passwords:** `password123`

## ✅ What Changed

### Backend Fixes
1. **database.py** - Now imports DATABASE_URL and DATABASE_TYPE from config.py
2. **auth.py** - Login endpoint (already had proper validation)
3. **main.py** - Login & Register endpoints now properly convert User to UserOut schema

### Configuration
- **.env file created** - Pre-configured for MySQL:
  ```
  DATABASE_TYPE=mysql
  MYSQL_HOST=localhost
  MYSQL_PORT=3306
  MYSQL_DB=sokoyetu
  MYSQL_USER=root
  MYSQL_PASSWORD=
  ```

### Database
- **sokoyetu_mysql.sql** - Complete MySQL schema with:
  - 13 tables with proper foreign keys
  - 7 test users (customer, vendor, driver, admin roles)
  - Proper indexes for performance
  - All constraints and collations set

### Documentation
- **MYSQL_XAMPP_SETUP.md** - Complete setup guide with troubleshooting
- **CHANGELOG.md** - Tracks all changes made

## 🐛 If Login Still Fails

### Check 1: Is MySQL running?
```
curl http://localhost:3306
```
Should return connection error (MySQL is responding)

### Check 2: Check database exists
In phpMyAdmin:
1. Left sidebar should show **sokoyetu** database
2. Click it and expand
3. Should show **users** table with 7 rows

### Check 3: Backend logs
Look at terminal where `python main.py` is running for error messages

### Check 4: Test database connection
```python
python -c "
from config import DATABASE_URL
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)
conn = engine.connect()
print('✅ Database connection successful!')
conn.close()
"
```

### Check 5: Verify user password
```python
# In backend folder
python -c "
import sqlite3
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Test password hash
hashed = '\$2b\$12\$aAeiOtXUSThkAdViQ.T3xO8Bqkpa94o6QUDjAyhhFt7lKtk2jOie2'
result = pwd_context.verify('password123', hashed)
print(f'Password verification: {result}')
"
```

## 📦 Next Steps

1. ✅ MySQL running in XAMPP
2. ✅ Database imported from SQL file  
3. ✅ Backend started
4. ✅ Login working
5. ⏭️ **Start frontend:**
   ```
   cd e:\sokoyetu\frontend
   npm run dev
   ```
6. ⏭️ Open http://localhost:5173
7. ⏭️ Try logging in with test user

## 📞 Support

If you encounter issues:

1. **MySQL connection errors** → Check XAMPP MySQL is running
2. **Database doesn't exist** → Re-import sokoyetu_mysql.sql
3. **Login returns 500 error** → Check backend console for traceback
4. **"Invalid credentials" message** → Confirm email/password match test users
5. **Password hash errors** → Ensure bcrypt is installed: `pip install passlib bcrypt`

See **MYSQL_XAMPP_SETUP.md** for more detailed troubleshooting.
