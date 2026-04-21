from database import SessionLocal
import models

def check():
    db = SessionLocal()
    users = db.query(models.User).all()
    print("ID | Email | Role")
    print("-" * 30)
    for u in users:
        print(f"{u.id} | {u.email} | {u.role}")
    db.close()

if __name__ == "__main__":
    check()
