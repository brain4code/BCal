from sqlalchemy.orm import Session
from ..models.user import User
from ..core.security import get_password_hash
from ..core.database import SessionLocal


def init_db():
    """Initialize database with default admin user if no users exist."""
    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(User).count()
        
        if user_count == 0:
            # Create default admin user
            default_admin = User(
                email="admin@bcal.com",
                username="admin",
                full_name="BCal Administrator",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True,
                timezone="UTC",
                bio="Default system administrator"
            )
            
            db.add(default_admin)
            db.commit()
            
            print("✅ Default admin user created!")
            print("📧 Email: admin@bcal.com")
            print("🔑 Password: admin123")
            print("⚠️  Please change these credentials after first login!")
        else:
            print("ℹ️  Database already has users, skipping default admin creation.")
            
    except Exception as e:
        print(f"❌ Error creating default admin: {e}")
        db.rollback()
    finally:
        db.close()
