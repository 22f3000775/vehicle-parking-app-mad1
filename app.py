from flask import Flask
from flask_login import LoginManager
from backend.models import db, Admin, User
from datetime import datetime, timezone, timedelta

 
IST = timezone(timedelta(hours=0, minutes=0))

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

    @app.template_filter('to_ist')
    def to_ist_filter(utc_dt):
        if not utc_dt:
            return ''
    
    # If it's a string, convert to datetime
        if isinstance(utc_dt, str):
            try:
                utc_dt = datetime.fromisoformat(utc_dt)
            except ValueError:
                return utc_dt  # Return original if parsing fails

        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)

        return utc_dt.astimezone(IST).strftime('%Y-%m-%d %H:%M')

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)


