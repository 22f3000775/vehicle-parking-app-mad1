# backend/routes.py
from flask import Blueprint, render_template, request, redirect
from .models import db, User, Admin, ParkingLot, ParkingSpot, Reservation
from flask_login import login_user, login_required, current_user

routes_bp = Blueprint("routes_bp", __name__, template_folder="../templates")

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
    # Optional: categories (if used)
    #cats = db.session.query(ServiceCategory).all()

    # All user accounts except admin (if needed)
    active_users = db.session.query(User).all()
    #flagged_users = []  # or leave it out of the template


    # Parking lot and occupancy stats
    lot_count = db.session.query(ParkingLot).count()
    total_spots = db.session.query(ParkingSpot).count()
    occupied_spots = db.session.query(ParkingSpot).filter_by(status="Occupied").count()

    occupancy = round((occupied_spots / total_spots) * 100, 2) if total_spots else 0

    recent_actions = [
        "Created new lot 'Central Plaza'",
        "Flagged user: user123@example.com",
        "Updated slot availability in 'North Wing'"
    ]

    return render_template("admin/dashboard.html",
                           current_admin=current_user,
                           #all_cats=cats,
                           active_cust=active_users,
                           #flagged_cust=flagged_users,
                           lot_count=lot_count,
                           occupancy=occupancy,
                           recent_actions=recent_actions)



@routes_bp.route("/user/dashboard", methods=["GET", "POST"])
@login_required
def user_dashboard():
    # Get all reservations made by this user
    active_bookings = Reservation.query.filter_by(user_id=current_user.id, status="Active").all()
    inactive_bookings = Reservation.query.filter_by(user_id=current_user.id, status="Inactive").all()

    # Notifications (example placeholder - you can implement logic later)
    notifications = [
        {"type": "info", "message": "Your booking at City Center expires in 2 hours."},
        {"type": "success", "message": "Reservation confirmed for Park Avenue Lot."}
    ]

    # Saved spots — not currently in your schema, so leaving as empty list
    saved_spots = []  # Optional: implement if you add a 'favorites' table or user-saved spots

    return render_template("user/dashboard.html",
                           current_user=current_user,
                           active_bookings=active_bookings,
                           inactive_bookings=inactive_bookings,
                           notifications=notifications,
                           saved_spots=saved_spots)

