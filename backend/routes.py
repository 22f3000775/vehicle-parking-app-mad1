from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from .models import db, User, Admin, ParkingLot, ParkingSpot, Reservation, Vehicle
from flask_login import login_user, login_required, current_user, logout_user
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_
from sqlalchemy.exc import OperationalError

IST = timezone(timedelta(hours=5, minutes=30))


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
    occupied_spot_count = ParkingSpot.query.filter_by(status='Occupied').count()
    occupancy = round((occupied_spot_count / total_spots) * 100, 2) if total_spots else 0
    
    

    return render_template("admin/dashboard.html",
                           current_admin=current_user,
                           active_cust=active_users,
                           lot_count=lot_count,
                           occupancy=occupancy,
                           occupied_spot_count=occupied_spot_count,
                           )

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
        address = lot.address
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status="Occupied").count()
        lot_data.append({
            "id": lot.id,
            "name": f"Lot {lot.id}",
            "total_spots": total_spots,
            "occupied_spots": occupied_spots,
            "address": address
        })

    return render_template("admin/parking_lots.html", lot_data=lot_data)

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

    current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
    current_spot_count = len(current_spots)

    if new_no_of_spots > current_spot_count:
    
        for i in range(current_spot_count, new_no_of_spots):
            spot = ParkingSpot(
                lot_id=lot.id,
                spot_number=f"S{i+1}",
                status="Available"
            )
            db.session.add(spot)
    elif new_no_of_spots < current_spot_count:
  
        spots_to_remove = current_spots[new_no_of_spots:]
        for spot in spots_to_remove:
            if spot.status == "Available":
                db.session.delete(spot)
            else:
                flash(f"Cannot remove spot {spot.spot_number} as it is occupied.", "warning")
  
    db.session.commit()
    flash(f"Number of spots for lot '{lot.location}' updated successfully.", "success")
    return redirect(url_for("routes_bp.admin_lots"))

@routes_bp.route("/admin/lots/<int:lot_id>/delete", methods=["POST"])
@login_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)

    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status="Occupied").count()
    if occupied_spots > 0:
        flash("Cannot delete lot with occupied spots.", "danger")
        return redirect(url_for("routes_bp.admin_lots"))

    ParkingSpot.query.filter_by(lot_id=lot.id).delete()

    db.session.delete(lot)
    db.session.commit()

    flash(f"Parking lot '{lot.location}' deleted successfully.", "success")
    return redirect(url_for("routes_bp.admin_lots"))

@routes_bp.route('/occupied_spot_details', methods = ["GET", "POST"])
@login_required
def occupied_spot_details():
    now = datetime.now(IST)
    
    occupied_reservations = Reservation.query.filter_by(status="Active").all()

    spot_details = []
    for res in occupied_reservations:
        spot = res.spot
        lot = spot.lot if spot else None
        user = res.user
        vehicle = res.vehicle

        entry_time = res.entry_ts.strftime("%Y-%m-%d %H:%M")
        exit_time = res.exit_ts.strftime("%Y-%m-%d %H:%M") if res.exit_ts else 'Ongoing'
        if res.exit_ts:
            duration = int((res.exit_ts - res.entry_ts).total_seconds() // 60)
        else:
            duration = int((now - res.entry_ts).total_seconds() // 60)
        cost = res.cost if res.cost is not None else 'N/A'

        spot_details.append({
            'spot_number': spot.spot_number if spot else 'N/A',
            'lot_name': lot.address if lot else 'N/A',
            'user_name': user.name if user else 'N/A',
            'vehicle_type': vehicle.vehicle_type if vehicle else 'N/A',
            'vehicle_number': vehicle.vehicle_number if vehicle else 'N/A',
            'entry_ts': entry_time,
            'exit_ts': exit_time,
            'duration_mins': duration,
            'cost': cost
        })

    return render_template('admin/occupied_spots.html', spot_details=spot_details)


@routes_bp.route('/admin/analytics', methods = ["GET", "POST"])
@login_required
def admin_analytics():
    now = datetime.now(IST)

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

    active_count = Reservation.query.filter(
        Reservation.status == "Active",
        Reservation.entry_ts <= now
    ).count()


    scheduled_count = Reservation.query.filter(
        Reservation.status == 'Scheduled'
        #Reservation.entry_ts > now
    ).count()

    
    active_reservations = Reservation.query.filter(
        Reservation.status == "Active",
        Reservation.entry_ts <= now
    ).all()


    total_revenue = 0
    for res in active_reservations:
        price_per_hour = res.spot.lot.price  
        end_time = res.exit_ts or now
        duration_seconds = (end_time - res.entry_ts).total_seconds()
        duration_hours = max(duration_seconds / 3600, 0)
        total_revenue += price_per_hour * duration_hours

    total_lots_created = len(parking_lots)

   
    total_reservations = Reservation.query.filter(
        Reservation.status.in_(['Active', 'Scheduled'])
    ).count()

    return render_template(
        'admin/analytics.html',
        lots_data=lots_data,
        total_lots_created=total_lots_created,
        total_reservations=total_reservations,
        active_count=active_count,
        scheduled_count=scheduled_count,
        total_revenue=total_revenue,
        active_reservations = active_reservations
    )


@routes_bp.route('/admin/all_parking_records', methods=['GET'])
@login_required
def all_parking_records():
   
    reservations = Reservation.query.order_by(Reservation.entry_ts.desc()).all()

    records = []
    for res in reservations:
        user = res.user
        vehicle = res.vehicle
        lot = res.spot.lot
        spot = res.spot

        entry = res.entry_ts.astimezone(IST) if res.entry_ts else None
        exit_ = res.exit_ts.astimezone(IST) if res.exit_ts else None
        duration_hours = None

        if entry and exit_:
            duration_seconds = (exit_ - entry).total_seconds()
            duration_hours = round(duration_seconds / 3600, 2)

        records.append({
            "user_name": user.name,
            "user_email": user.email,
            "vehicle_number": vehicle.vehicle_number if vehicle else "N/A",
            "lot_address": lot.address,
            "spot_id": spot.id,
            "entry_ts": entry.strftime('%Y-%m-%d %H:%M:%S') if entry else "N/A",
            "exit_ts": exit_.strftime('%Y-%m-%d %H:%M:%S') if exit_ else "N/A",
            "duration": f"{duration_hours} hrs" if duration_hours else "N/A",
            "cost": f"₹{res.cost:.2f}" if res.cost else "₹0.00",
            "status": res.status,
        })

    return render_template('admin/all_parking_records.html', records=records)


@routes_bp.route("/user/dashboard", methods=["GET", "POST"])
@login_required
def user_dashboard():
    expire_old_reservations()

    active_bookings = Reservation.query.filter_by(user_id=current_user.id, status="Active").all()
    inactive_bookings = Reservation.query.filter_by(user_id=current_user.id, status="Inactive").all()
    parking_lots = ParkingLot.query.all()

    now = datetime.now(IST)  # ✅ Correct


    
        
    scheduled_bookings = (
        Reservation.query
        .filter(
            Reservation.user_id == current_user.id,
            Reservation.status == 'Scheduled'
        )
        .order_by(Reservation.entry_ts.asc())
        .all()
    )
    
    inactive_bookings = Reservation.query.filter_by(user_id=current_user.id, status="Inactive").all()
    
    locations_query = db.session.query(ParkingLot.location).distinct().all()
    locations = [loc[0] for loc in locations_query]
    
    lots = ParkingLot.query.all()
      
    return render_template(
        "user/dashboard.html",
        current_user=current_user,
        active_bookings=active_bookings,
        scheduled_bookings=scheduled_bookings,
        inactive_bookings=inactive_bookings,
        locations=locations,
        parking_lots=lots
    )

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

from pytz import timezone
IST = timezone('Asia/Kolkata')

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

    try:
        vehicle = Vehicle.query.filter_by(user_id=current_user.id, vehicle_number=vehicle_number).first()
        if not vehicle:
            vehicle = Vehicle(user_id=current_user.id, vehicle_type=vehicle_type, vehicle_number=vehicle_number)
            db.session.add(vehicle)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("Vehicle entry failed. Try again.", "danger")
        print("Vehicle insert error:", e)
        return redirect(url_for('routes_bp.spot_booking_location', location=lot.location))

    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status="Available").order_by(ParkingSpot.id).first()
    if not spot:
        flash("No spots available in this lot.", "danger")
        return redirect(url_for('routes_bp.spot_booking_location', location=lot.location))

    try:
        start_datetime = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
        start_datetime = IST.localize(start_datetime)

    except ValueError:
        flash("Invalid date or time format.", "danger")
        return redirect(url_for('routes_bp.spot_booking_location', location=lot.location))

    end_datetime = start_datetime + timedelta(hours=booking_duration)
    now = datetime.now(IST)

    if start_datetime > now:
        reservation_status = "Scheduled"
        spot.status = "Booked"
    else:
        reservation_status = "Active"
        spot.status = "Occupied"

    
    try:
        new_reservation = Reservation(
            spot_id=spot.id,
            user_id=current_user.id,
            status=reservation_status,
            cost=lot.price * booking_duration,
            vehicle_id=vehicle.id,
            entry_ts=start_datetime,
            exit_ts=end_datetime,
        )
        db.session.add(new_reservation)
        db.session.add(spot) 
        db.session.commit()
        flash(f"Booking successful! Spot {spot.spot_number} assigned.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to book the spot. Try again.", "danger")
        print("Reservation insert error:", e)

    return redirect(url_for('routes_bp.user_dashboard'))


@routes_bp.route('/booking/end/<int:booking_id>', methods=['POST'])
@login_required
def end_booking(booking_id):
    booking = Reservation.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash("Unauthorized action", "danger")
        return redirect(url_for('routes_bp.user_dashboard'))

    booking.status = "Ended"
    booking.exit_ts = datetime.now(IST)

    spot = ParkingSpot.query.get(booking.spot_id)
    if spot:
        spot.status = "Available"

    db.session.commit()
    flash("Booking ended successfully.", "success")
    return redirect(url_for('routes_bp.user_dashboard'))

@routes_bp.route('/booking_summary', methods=['POST'])
def booking_summary():
    booking_id = request.form.get('booking_id')
    if not booking_id:
        return jsonify({'error': 'Booking ID missing'}), 400
    booking = Reservation.query.get(booking_id)
    if not booking or booking.status != 'Active':
        return jsonify({'error': 'Invalid or inactive booking.'}), 400

    booking.end_time = datetime.now(IST)
    if booking.entry_ts.tzinfo is None:
        booking.entry_ts = IST.localize(booking.entry_ts)
    duration_seconds = (booking.end_time - booking.entry_ts).total_seconds()
    duration_hours = duration_seconds / 3600
    price_per_hour = booking.spot.lot.price

    booking.cost = round(duration_hours * price_per_hour, 2)
    booking.status = 'Ended'
    spot = booking.spot
    spot = ParkingSpot.query.get(booking.spot_id)
    if spot:
        spot.status = "Available"
    else:
        print("Spot not found for booking ID:", booking.id)

    try:
        db.session.commit()
    except Exception as e:
        print("Commit failed:", e)
        db.session.rollback()


    summary = {
        'start_time': booking.entry_ts.strftime('%Y-%m-%d %H:%M'),
        'end_time': booking.end_time.strftime('%Y-%m-%d %H:%M'),
        'duration': round(duration_hours, 2),
        'rate': price_per_hour,
        'cost': booking.cost
    }
    return jsonify(summary)

@routes_bp.route('/user/history')
@login_required
def user_history():
    
    reservations = (
        Reservation.query
        .filter_by(user_id=current_user.id)
        .order_by(Reservation.entry_ts.desc())
        .all()
    )
    return render_template('user/user_history.html', reservations=reservations)


@routes_bp.route('/reservation/<int:res_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(res_id):
    reservation = Reservation.query.filter_by(id=res_id, user_id=current_user.id).first()

    if not reservation:
        flash("Reservation not found.", "error")
        return redirect(url_for('routes_bp.user_history'))

    entry_time = reservation.entry_ts
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=IST)

    if entry_time <= datetime.now(IST):
        flash("Cannot cancel booking that has already started or ended.", "error")
        return redirect(url_for('routes_bp.user_history'))

    reservation.status = 'Cancelled'
    reservation.exit_ts = datetime.now(IST)
    reservation.cost = 0
    reservation.spot.status = 'Available'

    db.session.commit()
    flash("Booking cancelled successfully.", "success")
    return redirect(url_for('routes_bp.user_history'))

    
def expire_old_reservations():
    try:
        now = datetime.now(IST) 
        expired = Reservation.query.filter(
            Reservation.exit_ts == None,
            Reservation.status == 'Active',
            Reservation.exit_ts <= now
        ).all()

        for res in expired:
            res.status = 'Expired'
            res.exit_ts = now
            res.spot.status = 'Available'

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print("DB rollback due to error in expire_old_reservations:", e)











