from .models import db, Admin



if db.session.query(Admin).count()==0:
    admin = Admin(name = "dodo", email= "dodo@myapp.com", password = "doe")
    db.session.add(admin)
    db.session.commit()