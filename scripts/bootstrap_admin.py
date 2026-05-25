"""Bootstrap admin user row by Telegram ID."""
from app.db.session import SessionLocal
from app.db.models import User

SUPER_ADMIN_ID = 6646320334


def main() -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == SUPER_ADMIN_ID).first()
        if not user:
            user = User(telegram_id=SUPER_ADMIN_ID, username="NexaNo1Support")
            db.add(user)
            db.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")
    finally:
        db.close()


if __name__ == "__main__":
    main()
