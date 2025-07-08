# backend/routes.py
from flask import Blueprint, render_template, request, redirect
from .models import db, User, Admin
from flask_login import login_user, login_required, current_user

routes_bp = Blueprint("routes", __name__)

@routes_bp.route("/")
def index():
    return render_template("home.html")

@routes_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    email = request.form.get("email")
    password = request.form.get("password")
    user_obj = None
    role = None

    admin = Admin.query.filter_by(email=email).first()
    if admin:
        user_obj = admin
        role = "admin"
    else:
        user = User.query.filter_by(email=email).first()
        if user:
            user_obj = user
            role = "user"

    if user_obj:
        if user_obj.password == password:
            login_user(user_obj)
            if role == "admin":
                return redirect("/admin/dashboard")
            return redirect("/user/dashboard")
        return "Incorrect Password"
    
    return "No account found with this email"

@routes_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("user/register.html")

    u_name = request.form.get("user_name") 
    u_email = request.form.get("user_email")
    u_password = request.form.get("user_password")
    u_address = request.form.get("user_address")
    u_phone = request.form.get("user_phone")

    if User.query.filter_by(email=u_email).first():
        return "Email already exists for user"
    
    new_user = User(
        name=u_name,
        email=u_email,
        password=u_password,
        address=u_address,
        phone=u_phone
    )
    db.session.add(new_user)
    db.session.commit()
    return redirect("/login")

@routes_bp.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    return render_template("admin/dashboard.html", current_admin=current_user)

@routes_bp.route("/user/dashboard", methods=["GET", "POST"])
@login_required
def user_dashboard():
    return render_template("user/dashboard.html", current_user=current_user)
