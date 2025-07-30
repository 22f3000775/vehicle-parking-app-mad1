# Vehicle Parking App 

This Vehicle Parking App streamlines parking management through user reservations, admin control, and cost tracking. Built by using Flask, SQLAlchemy, and Flask-Login for backend and Javascript and Bootstrap for frontend, it supports role-based access, efficient database handling, and timestamp-based billing—ideal for smart parking setups.

## Tech Stack

- Flask  
- Flask-SQLAlchemy  
- Flask-Login  
- SQLite (SQLAlchemy)  

## Key Features

- User registration and login  
- Admin-only login (predefined credentials)  
- Role-based dashboard redirection  
- Admin controls for parking lot and spot management  
- Automatic spot generation per lot capacity  
- User-side reservation and spot tracking  
- Timestamp-based cost calculation and history view  

## Models Overview

- Admin: Stores admin credentials and handles admin login  
- User: Handles user registration and details  
- ParkingLot: Basic metadata for each parking location  
- ParkingSpot: Links to ParkingLot and has status tracking  
- Vehicle: Stores user vehicle info for parking history  
- Reservation: Tracks entry/exit time, cost, and spot allocation  

## Timezone Setup

Use Indian Standard Time:

IST = timezone(timedelta(hours=5, minutes=30))

## Setup Instructions

1. Install required libraries:

    pip install flask flask_sqlalchemy flask_login

2. Initialize database:

    from app import db
    db.create_all()

3. Run the server:

    flask run


## Git Commit Flow (Milestones)

- Milestone-VP DB-Relationship  
- Milestone-VP Auth-RBAC  
- Milestone-VP Admin-Dashboard-Management  
- Milestone-VP User-Dashboard-Management  
- Milestone-VP Summary-Users-Admin  
- Milestone-VP Cost-Calculation  

## File tree

-app.py
-backend
┣ 📂__pycache__
┃ ┣ create_initial_db.cpython-311.pyc
┃ ┣ models.cpython-311.pyc
┃ ┗ routes.cpython-311.pyc
┣ create_initial_db.py
┣ models.py
┗ routes.py
-templates
┣ 📂admin
┃ ┣ all_parking_records.html
┃ ┣ analytics.html
┃ ┣ dashboard.html
┃ ┣ occupied_spots.html
┃ ┣ parking_lots.html
┃ ┗ user_info.html
┣ 📂user
┃ ┣ dashboard.html
┃ ┣ register.html
┃ ┣ spot_booking_location.html
┃ ┗ user_history.html
┣ home.html
┗ login.html


