from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone
from flask_login import UserMixin

db = SQLAlchemy()

class Admin(db.Model, UserMixin):
    __tablename__ = "Admin"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable = False)
    email = db.Column(db.String, unique =True, nullable = False)
    password = db.Column(db.String, nullable = False)

    def get_id(self):
        return self.email

class User(db.Model, UserMixin):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable = False)
    email = db.Column(db.String, unique =True, nullable = False)
    password = db.Column(db.String, nullable = False)
    address = db.Column(db.String, nullable = False)
    phone = db.Column(db.String, nullable = False)

    def get_id(self):
        return self.email

class ParkingLot(db.Model):
    __tablename__ = "ParkingLot"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    location = db.Column(db.String, nullable = False)
    address = db.Column(db.String, nullable = False)
    price = db.Column(db.Integer, nullable = False)
    no_of_spots = db.Column(db.Integer, nullable = False)
    
class ParkingSpot(db.Model):
    __tablename__ = "ParkingSpot"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    lot_id= db.Column(db.Integer, db.ForeignKey("ParkingLot.id"), nullable = False)
    status = db.Column(db.String, nullable = False)
    spot_number= db.Column(db.String, nullable = False)
    lot = db.relationship("ParkingLot", backref = "spots")

    __table_args__ = (
        db.UniqueConstraint('lot_id', 'spot_number', name='_lot_spot'),
    )

class Reservation(db.Model):
    __tablename__ = "Reservation"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    spot_id = db.Column(db.Integer, db.ForeignKey("ParkingSpot.id"), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable = False) 
    vehicle_id = db.Column(db.Integer, db.ForeignKey("Vehicle.id"), nullable=True)
    status = db.Column(db.String, nullable = False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    entry_ts = db.Column(db.DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))
    exit_ts = db.Column(db.DateTime(timezone=True))
    user = db.relationship("User", backref = "reservations")
    spot = db.relationship("ParkingSpot", backref = "reservations")
    vehicle = db.relationship("Vehicle", backref="reservations")

class Vehicle(db.Model):
    __tablename__ = "Vehicle"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id= db.Column(db.Integer, db.ForeignKey("User.id"), nullable = False)
    vehicle_type = db.Column(db.String, nullable = False)
    vehicle_number= db.Column(db.String, unique = True, nullable = False)    
    user = db.relationship("User", backref = "vehicles")
