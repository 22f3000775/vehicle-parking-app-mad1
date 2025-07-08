# backend/create_initial_db.py
def init_db(app):
    from backend.models import db, Admin, User

    with app.app_context():
        if db.session.query(Admin).count() == 0:
            admin = Admin(name="dodo", email="dodo@myapp.com", password="doe")
            db.session.add(admin)

        if db.session.query(User).count() == 0:
            users = [
                User(name="Ram", email="Ram@myapp.com", password="pass", address="Jaipur", phone="9999999999"),
                User(name="Shyam", email="Shyam@myapp.com", password="pass", address="Delhi", phone="9999999999"),
                User(name="Prakash", email="Prakash@myapp.com", password="pass", address="Delhi", phone="9999999999"),
            ]
            db.session.add_all(users)

        db.session.commit()
