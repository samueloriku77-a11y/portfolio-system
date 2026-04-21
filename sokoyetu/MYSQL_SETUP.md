# MySQL Migration from SQLite (XAMPP)

## 1. Start XAMPP MySQL
- Open XAMPP Control Panel
- Start Apache + MySQL

## 2. Create Database
- Open phpMyAdmin (http://localhost/phpmyadmin)
- Run `e:/sokoyetu/sokoyetu_mysql.sql` → Creates 'sokoyetu' DB + tables + test data (incl. admin@test.com)

## 3. Configure .env (create/edit in root)
```
DATABASE_TYPE=mysql
MYSQL_USER=root
MYSQL_PASSWORD=  # Leave empty if no pw
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=sokoyetu
```

## 4. Backend Migration
```
cd backend
pip install pymysql  # MySQL driver
python migrate.py    # Migrate data if needed
uvicorn main:app --reload
```

## 5. Verify
- Backend API: http://localhost:8000/docs
- Login as admin@test.com / password123

Test users ready. Scalable MySQL now live! 🚀
