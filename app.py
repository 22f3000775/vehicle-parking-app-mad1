from flask import Flask
from flask_login import LoginManager
from backend.models import db, Admin, User

def create_app():
    app = Flask(__name__)

   
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vehicle_db.sqlite3"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "myspoton"

    db.init_app(app)
   
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.filter_by(email=user_id).first() or User.query.filter_by(email=user_id).first()

    with app.app_context():
        db.create_all()

        from backend.create_initial_db import init_db
        init_db(app)

        from backend.routes import routes_bp
        app.register_blueprint(routes_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
