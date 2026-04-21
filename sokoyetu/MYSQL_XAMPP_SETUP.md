# SokoYetu MySQL Setup with XAMPP

## Step 1: Start XAMPP MySQL

1. Open **XAMPP Control Panel**
2. Click the **Start** button next to **MySQL**
   - You should see "Running" status and green highlight
3. Note the port (default is **3306**)

## Step 2: Import the SQL File

### Option A: Using phpMyAdmin (Easiest)

1. In XAMPP Control Panel, click **Admin** next to MySQL
   - This opens phpMyAdmin in your browser
2. In phpMyAdmin:
   - Click **"Import"** tab at the top
   - Click **"Choose File"** and select `sokoyetu_mysql.sql`
   - Click **"Go"** or **"Import"** button
3. You should see green success message: "Import has been executed successfully"

### Option B: Using MySQL Command Line

1. Open **Command Prompt** or **PowerShell**
2. Navigate to MySQL bin folder:
   ```
   cd "C:\xampp\mysql\bin"
   ```
3. Run this command to import the SQL file:
   ```
   mysql -u root < "C:\path\to\sokoyetu_mysql.sql"
   ```
   Replace the path with actual location of `sokoyetu_mysql.sql`

### Option C: Using MySQL Workbench (If Installed)

1. Open **MySQL Workbench**
2. Connect to your MySQL server
3. File → Open SQL Script → Select `sokoyetu_mysql.sql`
4. Click the Execute button (lightning bolt icon)

## Step 3: Verify Database Created

In phpMyAdmin:
1. Left sidebar should show **sokoyetu** database
2. Click on it to expand
3. You should see these tables:
   - users (7 test users)
   - products
   - product_images
   - orders
   - order_items
   - ledgers
   - handshake_keys
   - delivery_verifications
   - driver_locations
   - payments
   - wallet_transactions
   - disputes
   - notifications

## Step 4: Configure Backend

The `.env` file is already set to MySQL:
```
DATABASE_TYPE=mysql
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=sokoyetu
```

If your MySQL has a password, update:
```
MYSQL_PASSWORD=your_password_here
```

## Step 5: Start Backend

```
cd e:\sokoyetu\backend
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 6: Test Login

### Using curl:
```
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer1@test.com","password":"password123"}'
```

### Using frontend:
1. Open http://localhost:5173 (or your frontend URL)
2. Try logging in with:
   - **Email**: customer1@test.com
   - **Password**: password123
   - **Role**: CUSTOMER

## Test Users

All test users have password: **password123**

| Email | Password | Role |
|-------|----------|------|
| customer1@test.com | password123 | CUSTOMER |
| customer2@test.com | password123 | CUSTOMER |
| vendor1@test.com | password123 | VENDOR |
| vendor2@test.com | password123 | VENDOR |
| driver1@test.com | password123 | DRIVER |
| driver2@test.com | password123 | DRIVER |
| admin@test.com | password123 | ADMIN |

## Troubleshooting

### "Access denied for user 'root'@'localhost'"
- Check if MySQL is running in XAMPP Control Panel
- If you have a MySQL password, update `.env` with `MYSQL_PASSWORD=your_password`

### "Can't connect to MySQL server on 'localhost' (10061)"
- Make sure XAMPP MySQL is running (green highlight in Control Panel)
- Check if port 3306 is already in use: `netstat -ano | findstr :3306`

### "Database 'sokoyetu' doesn't exist"
- The SQL file should create it, but try again from Step 2
- Make sure the SQL file imported without errors

### PHP/phpMyAdmin not loading
- In XAMPP Control Panel, also start **Apache**
- Then access http://localhost/phpmyadmin

## Backup & Reset

### To backup current database:
```
cd "C:\xampp\mysql\bin"
mysqldump -u root sokoyetu > backup.sql
```

### To reset and reload:
1. In phpMyAdmin, select sokoyetu database
2. Click "Drop" to delete all data
3. Re-import the SQL file from Step 2

## Next Steps

✅ Database is set up with MySQL via XAMPP  
✅ Test users are loaded  
✅ Backend can now connect to MySQL  
✅ Try logging in from frontend or curl  

If login still doesn't work, check backend console for error messages when you attempt login.
