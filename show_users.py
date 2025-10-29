from app import app, db, User

def show_users():
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("ჯერ არავინ დარეგისტრირებულა")
            return
        
        print("=== დარეგისტრირებული მომხმარებლები ===")
        print()
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"სახელი: {user.name}")
            print(f"Email: {user.email}")
            print(f"Email ვერიფიცირებული: {'კი' if user.email_verified else 'არა'}")
            print(f"რეგისტრაციის თარიღი: {user.created_at}")
            print("-" * 40)

if __name__ == "__main__":
    show_users()