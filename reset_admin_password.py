#!/usr/bin/env python3
"""
Admin Password Reset Tool
ადმინისტრატორის პაროლის გადატანა
"""

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def reset_admin_password():
    with app.app_context():
        print("🔄 ადმინისტრატორის პაროლის გადატანა...")
        print("=" * 50)
        
        # Find existing user
        user = User.query.filter_by(email='alambarimalambari@gmail.com').first()
        
        if user:
            print(f"✅ მომხმარებელი ნაპოვნია: {user.name} ({user.email})")
            
            # Set new simple password
            new_password = "admin123"
            user.set_password(new_password)
            user.email_verified = True  # Make sure it's verified
            
            db.session.commit()
            
            print(f"🔑 ახალი პაროლი დაყენებულია: {new_password}")
            print(f"📧 ელ-ფოსტა: {user.email}")
            print(f"👤 სახელი: {user.name}")
            print("✅ ანგარიში ვერიფიცირებულია")
            print()
            print("🌐 ლინკები:")
            print("   მთავარი გვერდი: http://127.0.0.1:5001/")
            print("   ლოგინი: http://127.0.0.1:5001/login")
            print("   ადმინ პანელი: http://127.0.0.1:5001/admin")
            print("   ბაზის ნახვა: http://127.0.0.1:5001/admin/database")
            
        else:
            print("❌ მომხმარებელი ვერ ნაპოვნია")
            
            # Create new admin user
            print("🆕 ახალი ადმინ ანგარიშის შექმნა...")
            new_user = User(
                name='alambari',
                email='alambarimalambari@gmail.com',
                email_verified=True
            )
            new_user.set_password('admin123')
            
            db.session.add(new_user)
            db.session.commit()
            
            print("✅ ახალი ანგარიში შექმნილია!")
            print(f"📧 ელ-ფოსტა: alambarimalambari@gmail.com")
            print(f"👤 სახელი: alambari")
            print(f"🔑 პაროლი: admin123")

if __name__ == '__main__':
    reset_admin_password()