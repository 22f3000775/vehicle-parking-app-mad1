# backend/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .models import db, User, Admin, ParkingLot, ParkingSpot, Reservation, Vehicle
from flask_login import login_user, login_required, current_user, logout_user
from datetime import datetime, timezone, timedelta


routes_bp = Blueprint("routes_bp", __name__, template_folder="../templates")

@routes_bp.route("/")
def home():
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


@routes_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes_bp.login'))


@routes_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("user/register.html")

    u_name = request.form.get("name") 
    u_email = request.form.get("email")
    u_password = request.form.get("password")
    u_address = request.form.get("address")
    u_phone = request.form.get("phone")

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
    
    active_users = db.session.query(User).all()
    
    lot_count = db.session.query(ParkingLot).count()
    total_spots = db.session.query(ParkingSpot).count()
    occupied_spots = db.session.query(ParkingSpot).filter_by(status="Occupied").count()

    occupancy = round((occupied_spots / total_spots) * 100, 2) if total_spots else 0
    occupied_spot_count = ParkingSpot.query.filter_by(status='Occupied').count()
    

    return render_template("admin/dashboard.html",
                           current_admin=current_user,
                           active_cust=active_users,
                           lot_count=lot_count,
                           occupancy=occupancy,
                           occupied_spot_count=occupied_spot_count,
                           )

@routes_bp.route("/admin/occupied-spots")
@login_required
def view_occupied_spots():
    # Fetch only spots that are currently occupied
    occupied_spots = ParkingSpot.query.filter_by(status='Occupied').all()

    active_reservations = []
    for spot in occupied_spots:
        reservation = Reservation.query.filter_by(spot_id=spot.id).order_by(Reservation.entry_ts.desc()).first()
        if reservation and reservation.exit_ts is None:
            active_reservations.append({
                "spot": spot,
                "reservation": reservation,
                "vehicle": reservation.vehicle,
                "user": reservation.user,
                "lot": spot.lot
            })

    return render_template("admin/occupied_spots.html", reservations=active_reservations)



@routes_bp.route("/admin/users", methods=["GET"])
@login_required
def view_users():
    users = db.session.query(User).all()
    return render_template("admin/user_info.html", users=users)

@routes_bp.route("/admin/lots", methods=["GET"])
@login_required
def admin_lots():
    lots = ParkingLot.query.all()

    lot_data = []
    for lot in lots:
        total_spots = lot.no_of_spots
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status="Occupied").count()
        lot_data.append({
            "id": lot.id,
            "name": f"Lot {lot.id}",
            "total_spots": total_spots,
            "occupied_spots": occupied_spots
        })

    return render_template("admin/parking_lots.html", lot_data=lot_data)

# Create New Lot (via modal)
@routes_bp.route("/admin/lots/create", methods=["POST"])
@login_required
def create_lot():
    location = request.form.get("location")
    address = request.form.get("address")
    price = request.form.get("price")
    no_of_spots = request.form.get("no_of_spots")

    if not (location and address and price and no_of_spots):
        flash("All fields are required", "danger")
        return redirect(url_for("routes_bp.admin_lots"))

    new_lot = ParkingLot(
        location=location,
        address=address,
        price=int(price),
        no_of_spots=int(no_of_spots)
    )
    db.session.add(new_lot)
    db.session.commit()

    # Optional: Auto-generate parking spots for this lot
    for i in range(new_lot.no_of_spots):
        spot = ParkingSpot(
            lot_id=new_lot.id,
            spot_number=f"S{i+1}",
            status="Available"
        )
        db.session.add(spot)
    db.session.commit()

    flash(f"Parking lot '{location}' created successfully.", "success")
    return redirect(url_for("routes_bp.admin_lots"))

@routes_bp.route("/admin/lots/<int:lot_id>/edit", methods=["POST"])
@login_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    new_no_of_spots = request.form.get("no_of_spots")

    if not new_no_of_spots or not new_no_of_spots.isdigit() or int(new_no_of_spots) < 1:
        flash("Please enter a valid positive number of spots.", "danger")
        return redirect(url_for("routes_bp.admin_lots"))

    new_no_of_spots = int(new_no_of_spots)
    old_no_of_spots = lot.no_of_spots

    if new_no_of_spots == old_no_of_spots:
        flash("Number of spots unchanged.", "info")
        return redirect(url_for("routes_bp.admin_lots"))

    lot.no_of_spots = new_no_of_spots
    db.session.commit()

    # Adjust associated parking spots:
    current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
    current_spot_count = len(current_spots)

    if new_no_of_spots > current_spot_count:
        # Add new available spots
        for i in range(current_spot_count, new_no_of_spots):
            spot = ParkingSpot(
                lot_id=lot.id,
                spot_number=f"S{i+1}",
                status="Available"
            )
            db.session.add(spot)
    elif new_no_of_spots < current_spot_count:
        # Remove spots beyond new number if they are Available
        spots_to_remove = current_spots[new_no_of_spots:]
        for spot in spots_to_remove:
            if spot.status == "Available":
                db.session.delete(spot)
            else:
                flash(f"Cannot remove spot {spot.spot_number} as it is occupied.", "warning")
                # Optionally, abort or skip removal
        # If you want, you can decide to block reducing spots if any are occupied

    db.session.commit()
    flash(f"Number of spots for lot '{lot.location}' updated successfully.", "success")
    return redirect(url_for("routes_bp.admin_lots"))

@routes_bp.route("/admin/lots/<int:lot_id>/delete", methods=["POST"])
@login_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    # Check if there are any occupied spots before deleting
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status="Occupied").count()
    if occupied_spots > 0:
        flash("Cannot delete lot with occupied spots.", "danger")
        return redirect(url_for("routes_bp.admin_lots"))

    # Delete all associated spots first
    ParkingSpot.query.filter_by(lot_id=lot.id).delete()

    # Then delete the lot itself
    db.session.delete(lot)
    db.session.commit()

    flash(f"Parking lot '{lot.location}' deleted successfully.", "success")
    return redirect(url_for("routes_bp.admin_lots"))

@routes_bp.route('/admin/analytics')
@login_required
def admin_analytics():
   
    parking_lots = ParkingLot.query.all()

    lots_data = []
    for lot in parking_lots:
        total_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status="Occupied").count()
        lots_data.append({
            'id': lot.id,
            'address': lot.address,
            'total_spots': total_spots,
            'occupied_spots': occupied_spots,
            'price': lot.price,
            'created_at': getattr(lot, 'created_at', None),
            'updated_at': getattr(lot, 'updated_at', None),
        })

    from sqlalchemy import func

    total_lots_created = len(parking_lots)
    total_reservations = Reservation.query.count()
    avg_duration = db.session.query(func.avg(func.julianday(Reservation.exit_ts) - func.julianday(Reservation.entry_ts))).scalar()
    total_revenue = db.session.query(func.sum(Reservation.cost)).scalar()

    return render_template('admin/analytics.html',
                           lots_data=lots_data,
                           total_lots_created=total_lots_created,
                           total_reservations=total_reservations,
                           avg_duration=avg_duration,
                           total_revenue=total_revenue)


@routes_bp.route("/user/dashboard", methods=["GET", "POST"])
@login_required
def user_dashboard():
    active_bookings = Reservation.query.filter_by(user_id=current_user.id, status="Active").all()
    inactive_bookings = Reservation.query.filter_by(user_id=current_user.id, status="Inactive").all()
    parking_lots = ParkingLot.query.all()

    now = datetime.now(timezone.utc)
    current_booking = Reservation.query.filter_by(user_id=current_user.id, status="Active") \
        .filter(Reservation.exit_ts >= now).first()

    saved_spots = []
    lots = ParkingLot.query.all()
    locations_query = db.session.query(ParkingLot.location).distinct().all()
    locations = [loc[0] for loc in locations_query]

    return render_template("user/dashboard.html",
                           current_user=current_user,
                           active_bookings=active_bookings,
                           inactive_bookings=inactive_bookings,
                           current_booking=current_booking,
                           locations=locations,
                           saved_spots=saved_spots,
                           parking_lots=lots)  



@routes_bp.route('/user/book/location/<location>')
@login_required
def spot_booking_location(location):
    lots = ParkingLot.query.filter_by(location=location).all()

    for lot in lots:
        lot.spots_available = ParkingSpot.query.filter_by(lot_id=lot.id, status="Available").count()

    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'user/spot_booking_location.html', 
        location=location, 
        parking_lots=lots,
        vehicles=vehicles,
    )



@routes_bp.route('/user/book/<int:lot_id>', methods=['POST'])
@login_required
def spot_booking(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    vehicle_type = request.form.get('vehicle_type')
    vehicle_number = request.form.get('vehicle_number')
    booking_date = request.form.get('booking_date')
    booking_time = request.form.get('booking_time')
    booking_duration = int(request.form.get('booking_duration', 1))

    if not all([vehicle_type, vehicle_number, booking_date, booking_time]):
        flash("All booking fields are required.", "danger")
        return redirect(url_for('routes_bp.spot_booking_location', location=lot.location))

    # Check if vehicle exists or create new
    vehicle = Vehicle.query.filter_by(user_id=current_user.id, vehicle_number=vehicle_number).first()
    if not vehicle:
        vehicle = Vehicle(user_id=current_user.id, vehicle_type=vehicle_type, vehicle_number=vehicle_number)
        db.session.add(vehicle)
        db.session.commit()

    # Find the first available parking spot in this lot
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status="Available").order_by(ParkingSpot.id).first()
    if not spot:
        flash("No spots available in this lot.", "danger")
        return redirect(url_for('routes_bp.spot_booking_location', location=lot.location))

    # Calculate booking datetime range
    try:
        start_datetime = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        flash("Invalid date or time format.", "danger")
        return redirect(url_for('routes_bp.spot_booking_location', location=lot.location))

    end_datetime = start_datetime + timedelta(hours=booking_duration)

    # Assign spot and create reservation
    spot.status = "Occupied"

    new_reservation = Reservation(
        spot_id=spot.id,
        user_id=current_user.id,
        status="Active",
        cost=lot.price * booking_duration,
        vehicle_id=vehicle.id,
        entry_ts=start_datetime,
        exit_ts=end_datetime,
    )
    db.session.add(new_reservation)
    db.session.commit()

    flash(f"Booking successful! Spot {spot.spot_number} assigned.", "success")
    return redirect(url_for('routes_bp.user_dashboard'))

@routes_bp.route('/booking/end/<int:booking_id>', methods=['POST'])
@login_required
def end_booking(booking_id):
    booking = Reservation.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for('routes_bp.user_dashboard'))

    booking.status = "Ended"
    booking.exit_ts = datetime.now(timezone.utc)

    spot = ParkingSpot.query.get(booking.spot_id)
    if spot:
        spot.status = "Available"

    db.session.commit()
    flash("Booking ended successfully.", "success")
    return redirect(url_for('routes_bp.user_dashboard'))











