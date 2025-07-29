# backend/create_initial_db.py
def init_db(app):
    from backend.models import db, Admin, User

    with app.app_context():
        if db.session.query(Admin).count() == 0:
            admin = Admin(name="Admin", email="admin@myapp.com", password="admin")
            db.session.add(admin)

        if db.session.query(User).count() == 0:
            users = [
                User(name="Ram", email="ram@myapp.com", password="pass", address="Jaipur", phone="9999999999"),
                User(name="Shyam", email="shyam@myapp.com", password="pass", address="Delhi", phone="9999999999"),
                User(name="Prajakta", email="prajakta@myapp.com", password="pass", address="Mysore", phone="9999999999"),
            ]
            db.session.add_all(users)

        db.session.commit()
