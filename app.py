from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from datetime import timedelta, datetime
from urllib.parse import urlparse, urljoin, quote, unquote, urlencode
import subprocess
import mysql.connector
import os  # Needed for environment variable access
from bson import ObjectId
from bson.errors import InvalidId

# Create a connection to MariaDB
def get_db_connection():
    return mysql.connector.connect(
        host='mariadb',
        user='user',
        password='upass',
        database='hotelbooking'
    )

# Dummy functions for filter values (can be replaced with actual DB queries)
def get_guests_from_mariadb():
    return ['1 Adult', '2 Adults', '3 Adults']

def get_rooms_from_mariadb():
    return ['1 Room', '2 Rooms', 'Suite']

def get_guests_from_mongodb():
    return ['1 Adult', '2 Adults', '3 Adults']

def get_rooms_from_mongodb():
    return ['1 Room', '2 Rooms', 'Suite']

# MongoDB connection
client = MongoClient("mongodb://mongo:27017/")
db = client["hotel-booking-platform"]

app = Flask(__name__)
app.secret_key = 'verysecretkey'
app.permanent_session_lifetime = timedelta(minutes=30)


# Homepage with filters
@app.route('/')
def index():
    current_db = session.get('active_db', 'mariadb')
    if current_db == 'mariadb':
        guest_options = get_guests_from_mariadb()
        room_options = get_rooms_from_mariadb()
    elif current_db == 'mongodb':
        guest_options = get_guests_from_mongodb()
        room_options = get_rooms_from_mongodb()
    else:
        guest_options = []
        room_options = []

    return render_template('index.html',
                           guest_options=guest_options,
                           room_options=room_options)



# Rooms listing with filtering logic
@app.route('/rooms')
def rooms():
    db_type = session.get("active_db", "mariadb")

    # Get filter parameters from query string
    checkin = request.args.get("date_in")
    checkout = request.args.get("date_out")
    guests = request.args.get("guests")
    room_type = request.args.get("room")

    available_rooms = []

    # Convert dates to datetime objects if provided
    checkin_date, checkout_date = None, None
    if checkin and checkout:
        try:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
            if checkin_date >= checkout_date:
                flash("⚠️ Check-out date must be after check-in date.", "danger")
                return render_template("rooms.html", rooms=[], checkin=checkin, checkout=checkout, guests=guests, room_type=room_type)
        except ValueError:
            flash("⚠️ Invalid date format.", "danger")
            return render_template("rooms.html", rooms=[], checkin=checkin, checkout=checkout, guests=guests, room_type=room_type)

    # Convert back to string format for query use
    checkin_str = checkin_date.strftime("%Y-%m-%d") if checkin_date else None
    checkout_str = checkout_date.strftime("%Y-%m-%d") if checkout_date else None

    if db_type == "mongodb":
        # MongoDB: Base query
        room_query = {"Status": "available"}
        if guests and guests.isdigit():
            room_query["MaxGuests"] = {"$gte": int(guests)}
        all_rooms = list(db.room.find(room_query))

        # Room type filter
        if room_type == "Suite":
            suite_numbers = set(r["RoomNumber"] for r in db.suiteroom.find())
            all_rooms = [r for r in all_rooms if r["RoomNumber"] in suite_numbers]
        elif room_type == "Deluxe":
            deluxe_numbers = set(r["RoomNumber"] for r in db.deluxeroom.find())
            all_rooms = [r for r in all_rooms if r["RoomNumber"] in deluxe_numbers]

        # Filter out booked rooms
        if checkin_str and checkout_str:
            booked = db.contains.aggregate([
                {
                    "$lookup": {
                        "from": "booking",
                        "localField": "BookingID",
                        "foreignField": "BookingID",
                        "as": "booking"
                    }
                },
                {"$unwind": "$booking"},
                {"$match": {
                    "$or": [
                        {"booking.CheckinDate": {"$lt": checkout_str, "$gte": checkin_str}},
                        {"booking.CheckOutDate": {"$gt": checkin_str, "$lte": checkout_str}},
                        {"booking.CheckinDate": {"$lte": checkin_str}, "booking.CheckOutDate": {"$gte": checkout_str}},
                    ]
                }},
                {"$project": {"RoomNumber": 1}}
            ])
            booked_numbers = set(b["RoomNumber"] for b in booked)
            all_rooms = [r for r in all_rooms if r["RoomNumber"] not in booked_numbers]

        available_rooms = all_rooms

    else:
        # MariaDB: Build dynamic SQL query
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM Room WHERE Status = 'available'"
        params = []

        if guests and guests.isdigit():
            query += " AND MaxGuests >= %s"
            params.append(int(guests))

        if room_type == "Suite":
            query += " AND RoomNumber IN (SELECT RoomNumber FROM SuiteRoom)"
        elif room_type == "Deluxe":
            query += " AND RoomNumber IN (SELECT RoomNumber FROM DeluxeRoom)"

        cursor.execute(query, params)
        all_rooms = cursor.fetchall()

        # Filter out booked rooms
        if checkin_str and checkout_str:
            cursor.execute("""
                SELECT DISTINCT c.RoomNumber
                FROM Contains c
                JOIN Booking b ON c.BookingID = b.BookingID
                WHERE NOT (b.CheckOutDate <= %s OR b.CheckinDate >= %s)
            """, (checkin_str, checkout_str))
            booked_numbers = set(row["RoomNumber"] for row in cursor.fetchall())
            available_rooms = [r for r in all_rooms if r["RoomNumber"] not in booked_numbers]
        else:
            available_rooms = all_rooms

        cursor.close()
        conn.close()

    return render_template(
        "rooms.html",
        rooms=available_rooms,
        checkin=checkin,
        checkout=checkout,
        guests=guests,
        room_type=room_type
    )




# Room details (static or dummy page)
@app.route('/room-details')
def rooms_details():
    return render_template('room-details.html')

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# SHOGOFA CHANGES *********************************************************************************************************************
import urllib.parse

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or request.form.get('next')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_type = session.get('active_db', 'mariadb')
        user = None

        if db_type == 'mongodb':
            user = db.customer.find_one({'Username': username, 'Password': password})
            if user:
                session['customer_id'] = str(user['_id']) 
        else:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Customer WHERE Username=%s AND Password=%s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                session['customer_id'] = user['CustomerID']
                session['first_name'] = user['FirstName']  

        if user:
            # If there is a pending booking (unauthenticated attempt), handle it
            pending = session.pop('pending_booking', None)
            if pending:
                return redirect(url_for(
                    'complete_booking',
                    room_number=pending['room_number'],
                    checkin=pending['checkin'],
                    checkout=pending['checkout']
                ))

            # Always redirect to homepage after login
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', next=next_url)

    

    # Booking list
@app.route('/bookings')
def bookings():
    customer_id = session.get('customer_id')
    if not customer_id:
        flash("Please log in to view your bookings.", "warning")
        return redirect(url_for('login'))

    db_type = session.get('active_db', 'mariadb')
    user_exists = False

    # Check if the user still exists in the current database
    if db_type == 'mongodb':
        try:
            user_exists = db.customer.find_one({"_id": ObjectId(customer_id)}) is not None
        except Exception:
            user_exists = False
    else:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT 1 FROM Customer WHERE CustomerID = %s", (customer_id,))
        user_exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()

    if not user_exists:
        session.clear()
        flash("Your session has expired or user no longer exists. Please log in again.", "warning")
        return redirect(url_for('login'))

    # ------------------ MongoDB Booking List --------------------
    if db_type == 'mongodb':
        bookings = []
        try:
            cust_obj_id = ObjectId(customer_id)
        except Exception:
            cust_obj_id = customer_id  # fallback, just in case
        for b in db.booking.find({"CustomerID": cust_obj_id}):
            contains = list(db.contains.find({"BookingID": b["_id"]}))
            rooms = []
            hotels = set()
            for c in contains:
                room = db.room.find_one({"_id": c["RoomID"]})
                hotel = db.hotel.find_one({"_id": c["HotelID"]})
                if room and hotel:
                    rooms.append({
                        "RoomNumber": room["RoomNumber"],
                        "HotelName": hotel["Name"],
                        "PricePerNight": room.get("PricePerNight", 0)
                    })
                    hotels.add(hotel["Name"])
            payments = b.get("payments", [])
            is_paid = all(p["PaymentStatus"] == "completed" for p in payments) and payments
            has_pending = any(p["PaymentStatus"] == "pending" for p in payments)
            pending_amount = sum(p["Amount"] for p in payments if p["PaymentStatus"] == "pending")
            bookings.append({
                "_id": b["_id"],
                "TotalPrice": b["TotalPrice"],
                "CheckInDate": b["CheckInDate"],
                "CheckOutDate": b["CheckOutDate"],
                "Rooms": rooms,
                "Hotels": list(hotels),
                "NumRooms": len(rooms),
                "is_paid": is_paid,
                "has_pending": has_pending,
                "PendingAmount": pending_amount
            })
        return render_template('bookings.html', bookings=bookings)
    else:
        # MariaDB logic
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                b.BookingID, b.TotalPrice, b.CheckInDate, b.CheckOutDate,
                r.RoomNumber, r.PricePerNight, h.Name AS HotelName, h.Rating AS HotelRating,
                rv.Rating AS ReviewRating
            FROM Booking b
            JOIN Contains c ON b.BookingID = c.BookingID
            JOIN Room r ON c.HotelID = r.HotelID AND c.RoomNumber = r.RoomNumber
            JOIN Hotel h ON r.HotelID = h.HotelID
            LEFT JOIN (
                            SELECT CustomerID, HotelID, MAX(Rating) AS Rating
                            FROM Review
                            GROUP BY CustomerID, HotelID
                        ) rv ON rv.CustomerID = b.CustomerID AND rv.HotelID = h.HotelID
            WHERE b.CustomerID = %s
            ORDER BY b.BookingID DESC
        """, (customer_id,))
        rows = cursor.fetchall()

        # Group by BookingID
        bookings_dict = {}
        for row in rows:
            bid = row['BookingID']
            if bid not in bookings_dict:
                bookings_dict[bid] = {
                    'BookingID': bid,
                    'TotalPrice': row['TotalPrice'],
                    'CheckInDate': row['CheckInDate'],
                    'CheckOutDate': row['CheckOutDate'],
                    'Rooms': [],
                    'Hotels': set(),
                }
            bookings_dict[bid]['Rooms'].append({
                'RoomNumber': row['RoomNumber'],
                'HotelName': row['HotelName'],
                'PricePerNight': row['PricePerNight'],
                'HotelRating': row['HotelRating'],
                'ReviewRating': row['ReviewRating'],
            })
            bookings_dict[bid]['Hotels'].add(row['HotelName'])

        # Add payment status
        for booking in bookings_dict.values():
            cursor.execute("SELECT PaymentStatus, Amount FROM Payment WHERE BookingID = %s", (booking['BookingID'],))
            payment_rows = cursor.fetchall()
            booking['is_paid'] = all(row['PaymentStatus'] == 'completed' for row in payment_rows) and payment_rows
            booking['has_pending'] = any(row['PaymentStatus'] == 'pending' for row in payment_rows)
            booking['NumRooms'] = len(booking['Rooms'])
            booking['Hotels'] = list(booking['Hotels'])
            # Calculate pending amount
            booking['PendingAmount'] = sum(row['Amount'] for row in payment_rows if row['PaymentStatus'] == 'pending')

        cursor.close()
        conn.close()
        bookings = list(bookings_dict.values())
        return render_template('bookings.html', bookings=bookings)


# Payments list
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    db_type = session.get('active_db', 'mariadb')
    if db_type == 'mongodb':
        if request.method == 'POST':
            data = request.get_json()
            booking_id = data.get('booking_id')
            booking = db.booking.find_one({"_id": ObjectId(booking_id)})
            new_payments = data.get('payments', [])
            
            if not booking:
                return jsonify({"success": False, "error": "Booking not found"}), 404

            # Update the payments array
            existing_payments = booking.get("payments", [])
            for new_payment in new_payments:
                # Find the pending payment to update
                for payment in existing_payments:
                    if (
                        payment.get("PaymentNumber") == new_payment.get("PaymentNumber")
                        and payment.get("PaymentStatus") == "pending"
                    ):
                        # Update fields
                        payment.update(new_payment)
                        payment["PaymentStatus"] = "completed"
                        payment["PaymentDate"] = new_payment.get("PaymentDate")
                        payment["PaymentMethod"] = new_payment.get("PaymentMethod")
                        payment["CardNumber"] = new_payment.get("CardNumber")
                        payment["ExpiryDate"] = new_payment.get("ExpiryDate")
                        payment["CVV"] = new_payment.get("CVV")
            # Save back to DB
            db.booking.update_one(
                {"_id": ObjectId(booking_id)},
                {"$set": {"payments": existing_payments}}
            )
            return jsonify({"success": True})

        # GET: Show payment page
        booking_id = request.args.get('booking_id')
        booking = None
        if booking_id:
            booking = db.booking.find_one({"_id": ObjectId(booking_id)})
        booking_total = request.args.get('booking_total')

        if booking and "payments" in booking:
            pending_amount = sum(
                float(p.get("Amount", 0))
                for p in booking["payments"]
                if p.get("PaymentStatus") == "pending"
            )
        has_pending = pending_amount > 0
        try:
            booking_total = float(booking_total)
        except (TypeError, ValueError):
            booking_total = 0.0

        return render_template(
            'payment.html',
            booking_id=booking_id,
            booking_total=booking_total,
            pending_amount=pending_amount,
            has_pending=has_pending
        )
    else:
        # MariaDB logic
        if request.method == 'POST':
            # Handle AJAX/JSON payment submission
            data = request.get_json()
            payments = data.get('payments', [])
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                for payment in payments:
                    cursor.execute("""
                        INSERT INTO Payment
                        (BookingID, PaymentNumber, PaymentMethod, PaymentDate, PaymentStatus,
                        CardNumber, ExpiryDate, CVV, Amount)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            PaymentMethod=VALUES(PaymentMethod),
                            PaymentDate=VALUES(PaymentDate),
                            PaymentStatus=VALUES(PaymentStatus),
                            CardNumber=VALUES(CardNumber),
                            ExpiryDate=VALUES(ExpiryDate),
                            CVV=VALUES(CVV),
                            Amount=VALUES(Amount)
                    """, (
                        payment['BookingID'],
                        payment['PaymentNumber'],
                        payment['PaymentMethod'],
                        payment['PaymentDate'],
                        payment['PaymentStatus'],
                        payment['CardNumber'],
                        payment['ExpiryDate'],
                        payment['CVV'],
                        payment['Amount']
                    ))
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        # GET: Show payment page
        booking_id = request.args.get('booking_id')
        booking_total = request.args.get('booking_total')

        pending_amount = None
        has_pending = False
        if booking_id:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT Amount FROM Payment WHERE BookingID = %s AND PaymentStatus = 'pending' LIMIT 1",
                (booking_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                pending_amount = float(row['Amount'])
                has_pending = True

        try:
            booking_total = float(booking_total)
        except (TypeError, ValueError):
            booking_total = 0.0

        return render_template(
            'payment.html',
            booking_id=booking_id,
            booking_total=booking_total,
            pending_amount=pending_amount,
            has_pending=has_pending
        )


# Booking report page
@app.route('/booking_report', methods=['GET', 'POST'])
def booking_report():
    db_type = session.get('active_db', 'mariadb')
    from_date = to_date = None
    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

    if db_type == 'mongodb':
        # Convert dates to datetime for MongoDB
        from_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else None
        to_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else None

        pipeline = [
            {
                "$match": {
                    **({"CheckinDate": {"$gte": from_date}} if from_date else {}),
                    **({"CheckOutDate": {"$lte": to_date}} if to_date else {})
                }
            },
            {
                "$lookup": {
                    "from": "customer",
                    "localField": "CustomerID",
                    "foreignField": "CustomerID",
                    "as": "customer"
                }
            },
            {"$unwind": "$customer"},
            {
                "$lookup": {
                    "from": "contains",
                    "localField": "_id",  # Use _id here!
                    "foreignField": "BookingID",
                    "as": "contains"
                }
            },
            {"$unwind": "$contains"},
            {
                "$lookup": {
                    "from": "hotel",
                    "localField": "contains.HotelID",
                    "foreignField": "HotelID",
                    "as": "hotel"
                }
            },
            {"$unwind": "$hotel"},
            {
                "$group": {
                    "_id": {
                        "CustomerID": "$CustomerID",
                        "HotelID": "$contains.HotelID",
                        "CustomerName": {"$concat": ["$customer.FirstName", " ", "$customer.LastName"]},
                        "HotelName": "$hotel.Name"
                    },
                    "NumBookings": {"$addToSet": "$_id"},
                    "NumRooms": {"$sum": 1},
                    "TotalSpent": {
                        "$sum": {
                            "$sum": {
                                "$map": {
                                    "input": {"$ifNull": ["$payments", []]},
                                    "as": "p",
                                    "in": {"$toDouble": "$$p.Amount"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "CustomerName": "$_id.CustomerName",
                    "HotelName": "$_id.HotelName",
                    "NumBookings": {"$size": "$NumBookings"},
                    "NumRooms": 1,
                    "TotalSpent": 1
                }
            },
            {"$sort": {"CustomerName": 1, "HotelName": 1}}
        ]
        report = list(db.booking.aggregate(pipeline))

        # Summary: total customers and total revenue in the filtered range
        total_customers = len(set(r["CustomerName"] for r in report))
        total_revenue = sum(r["TotalSpent"] for r in report)

        return render_template(
            'booking_report.html',
            report=report,
            total_customers=total_customers,
            total_revenue=total_revenue,
            from_date=from_date,
            to_date=to_date
        )
    else:
        # MariaDB logic
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                CONCAT(c.FirstName, ' ', c.LastName) AS CustomerName,
                h.Name AS HotelName,
                COUNT(DISTINCT b.BookingID) AS NumBookings,
                COUNT(DISTINCT co.RoomNumber) AS NumRooms,
                COALESCE(SUM(p.Amount), 0) AS TotalSpent
            FROM Customer c
            JOIN Booking b ON c.CustomerID = b.CustomerID
            JOIN Contains co ON b.BookingID = co.BookingID
            JOIN Hotel h ON co.HotelID = h.HotelID
            LEFT JOIN Payment p ON b.BookingID = p.BookingID
            WHERE (%s IS NULL OR %s IS NULL OR (b.CheckInDate BETWEEN %s AND %s))
            GROUP BY c.CustomerID, h.HotelID, c.FirstName, c.LastName, h.Name
            ORDER BY CustomerName, HotelName
        """, (from_date, to_date, from_date, to_date))
        report = cursor.fetchall()

        # Summary: total customers and total revenue in the filtered range
        cursor.execute("""
            SELECT COUNT(DISTINCT b.CustomerID) AS TotalCustomers
            FROM Booking b
            WHERE (%s IS NULL OR %s IS NULL OR (b.CheckInDate BETWEEN %s AND %s))
        """, (from_date, to_date, from_date, to_date))
        total_customers = cursor.fetchone()['TotalCustomers']

        cursor.execute("""
            SELECT COALESCE(SUM(p.Amount), 0) AS TotalRevenue
            FROM Payment p
            JOIN Booking b ON p.BookingID = b.BookingID
            WHERE (%s IS NULL OR %s IS NULL OR (b.CheckInDate BETWEEN %s AND %s))
        """, (from_date, to_date, from_date, to_date))
        total_revenue = cursor.fetchone()['TotalRevenue']

        cursor.close()
        conn.close()
        return render_template(
            'booking_report.html',
            report=report,
            total_customers=total_customers,
            total_revenue=total_revenue,
            from_date=from_date,
            to_date=to_date
        )


# NELIN CHANGES *********************************************************************************************************************

@app.route('/start-booking/<room_number>')
def start_booking(room_number):
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')

    if 'customer_id' not in session:
        session['pending_booking'] = {
            'room_number': room_number,
            'checkin': checkin,
            'checkout': checkout
        }

        next_path = url_for('start_booking', room_number=room_number) + '?' + urlencode({
            'checkin': checkin,
            'checkout': checkout
        })
        return redirect(url_for('login', next=quote(next_path)))



    return redirect(url_for(
        'complete_booking',
        room_number=room_number,
        checkin=checkin,
        checkout=checkout
    ))

@app.route('/complete-booking')
def complete_booking():
    customer_id = session.get('customer_id')
    if not customer_id:
        flash("Login required.", "warning")
        return redirect(url_for('login'))

    room_number = request.args.get('room_number')
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')

    if not all([room_number, checkin, checkout]):
        flash("Missing booking data.", "danger")
        return redirect(url_for('index'))

    db_type = session.get('active_db', 'mariadb')

    if db_type == 'mongodb':
        try:
            nights = (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days
            room = db.room.find_one({"RoomNumber": room_number})
            if not room:
                flash("Room not found.", "danger")
                return redirect(url_for('index'))

            total_price = room.get("PricePerNight", 0) * nights

            booking = {
                "CustomerID": customer_id,
                "CheckinDate": checkin,
                "CheckOutDate": checkout,
                "TotalPrice": total_price
            }
            booking_result = db.booking.insert_one(booking)

            db.contains.insert_one({
                "BookingID": booking_result.inserted_id,
                "RoomNumber": room_number,
                "HotelID": room["HotelID"]
            })

            flash("Booking successful! (MongoDB)", "success")
            return redirect(url_for('booking_confirmation', booking_id=str(booking_result.inserted_id)))

        except Exception as e:
            flash(f"MongoDB Booking Error: {str(e)}", "danger")
            return redirect(url_for('index'))

    else:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT PricePerNight, HotelID FROM Room WHERE RoomNumber = %s", (room_number,))
            room = cursor.fetchone()

            if not room:
                flash("Room not found in Room table.", "danger")
                cursor.close()
                conn.close()
                return redirect(url_for('index'))

            nights = (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days
            total_price = room['PricePerNight'] * nights
            print("💰 Calculated total_price:", total_price)

            cursor.execute("""
                INSERT INTO Booking (CustomerID, CheckInDate, CheckOutDate, TotalPrice)
                VALUES (%s, %s, %s, %s)
            """, (customer_id, checkin, checkout, total_price))
            booking_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO Contains (BookingID, HotelID, RoomNumber)
                VALUES (%s, %s, %s)
            """, (booking_id, room['HotelID'], room_number))
        
            conn.commit()
            cursor.close()
            conn.close()

            flash("Booking successful! (MariaDB)", "success")
            return redirect(url_for('booking_confirmation', booking_id=booking_id))

        except Exception as e:
            print("Exception in complete_booking():", str(e))
            flash(f"MariaDB Booking Error: {str(e)}", "danger")
            return redirect(url_for('index'))

        
@app.route('/booking-confirmation')
def booking_confirmation():
    booking_id = request.args.get('booking_id')
    if not booking_id:
        flash("Missing booking ID", "danger")
        return redirect(url_for('index'))

    db_type = session.get('active_db', 'mariadb')
    customer_id = session.get('customer_id')

    if db_type == 'mongodb':
        from bson import ObjectId
        booking = db.booking.find_one({"_id": ObjectId(booking_id), "CustomerID": customer_id})
        contains = db.contains.find_one({"BookingID": ObjectId(booking_id)})

        if not booking or not contains:
            flash("Booking not found", "danger")
            return redirect(url_for('index'))

        room = db.room.find_one({"RoomNumber": contains["RoomNumber"]})
        hotel = db.hotel.find_one({"HotelID": contains["HotelID"]})

        return render_template("booking_confirmation.html", booking=booking, room=room, hotel=hotel)

    else:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.BookingID, b.TotalPrice, b.CheckInDate, b.CheckOutDate,
                r.RoomNumber, h.Name AS HotelName
            FROM Booking b
            JOIN Contains c ON b.BookingID = c.BookingID
            JOIN Room r ON c.RoomNumber = r.RoomNumber AND c.HotelID = r.HotelID
            JOIN Hotel h ON r.HotelID = h.HotelID
            WHERE b.BookingID = %s AND b.CustomerID = %s
        """, (booking_id, customer_id))

        booking = cursor.fetchone()
        cursor.close()
        conn.close()

        if not booking:
            flash("Booking not found", "danger")
            return redirect(url_for('index'))

        return render_template("booking_confirmation.html", booking=booking)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


@app.route('/room_report', methods=['GET', 'POST'])
def room_report():
    db_type = session.get('active_db', 'mariadb')

    if db_type == 'mongodb':
        # MongoDB: Generate the report for bookings longer than 5 days vs. 5 days or less
        pipeline = [
            {
                "$project": {
                    "DurationCategory": {
                        "$cond": {
                            "if": {"$gt": [{"$subtract": ["$CheckOutDate", "$CheckInDate"]}, 5]},
                            "then": "More than 5 days",
                            "else": "5 days or less"
                        }
                    },
                    "RoomNumber": 1
                }
            },
            {
                "$group": {
                    "_id": "$DurationCategory",
                    "NumBookings": {"$sum": 1},
                    "NumSuites": {
                        "$sum": {
                            "$cond": [{"$in": ["$RoomNumber", ["Suite"]]}, 1, 0]
                        }
                    },
                    "TotalBookings": {"$sum": 1}
                }
            }
        ]
        
        # Perform aggregation
        results = db.booking.aggregate(pipeline)
        report_data = list(results)

    else:
        # MariaDB Query for Room Booking Duration Report (Total Bookings and Suite Bookings)
        query = """
            SELECT 
                CASE
                    WHEN DATEDIFF(CheckOutDate, CheckInDate) > 5 THEN 'More than 5 days'
                    ELSE '5 days or less'
                END AS DurationCategory,
                COUNT(*) AS NumBookings,
                COUNT(DISTINCT CASE WHEN sr.RoomNumber IS NOT NULL THEN b.BookingID END) AS NumSuiteBookings,
                COUNT(*) AS TotalBookings
            FROM Booking b
            JOIN Contains c ON b.BookingID = c.BookingID
            JOIN Room r ON c.RoomNumber = r.RoomNumber
            LEFT JOIN SuiteRoom sr ON r.RoomNumber = sr.RoomNumber
            LEFT JOIN DeluxeRoom dr ON r.RoomNumber = dr.RoomNumber
            WHERE b.CheckInDate IS NOT NULL AND b.CheckOutDate IS NOT NULL
            GROUP BY DurationCategory
            ORDER BY DurationCategory;
        """
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        report_data = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('room_report.html', report_data=report_data)



#*********************************************************************************************************************************

# Static pages
@app.route('/about')
def about():
    return render_template('about-us.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog-details')
def blog_details():
    return render_template('blog-details.html')

# Admin panel
@app.route('/admin')
def admin_dashboard():
    return render_template("admin.html")


@app.route('/reset-mariadb')
def reset_mariadb():
    try:
        result = subprocess.run(['python3', 'mariadb_seeder.py'], capture_output=True, text=True)
        session.clear()  # Clear any login/session!
        if result.returncode == 0:
            session['active_db'] = 'mariadb'  # Switch to MariaDB after reset
            return render_template("admin.html", message="✅ MariaDB has been reset and repopulated with fake data. Now using MariaDB.")
        else:
            return render_template("admin.html", message=f"❌ Error during MariaDB reset: {result.stderr}")
    except Exception as e:
        return render_template("admin.html", message=f"❌ Exception occurred: {str(e)}")


@app.route('/migrate-sql-to-nosql')
def migrate_sql_to_nosql():
    try:
        result = subprocess.run(["python", "migrate_sql_to_nosql.py"], capture_output=True, text=True)
        session.clear()  # logout and wipe session
        if result.returncode == 0:
            session['active_db'] = 'mongodb'
            return redirect(url_for('index'))
        else:
            return render_template("admin.html", message=f"❌ Migration Error: {result.stderr}")
    except Exception as e:
        return render_template("admin.html", message=f"❌ Exception: {str(e)}")

@app.route('/activate-mariadb')
def activate_mariadb():
    session.clear()
    session['active_db'] = 'mariadb'
    return redirect(url_for('index'))

# Switch to MongoDB
@app.route('/activate-mongodb')
def activate_mongodb():
    session['active_db'] = 'mongodb'
    return redirect(url_for('index'))

# MongoDB API Endpoints (REST-like)
@app.route('/api/hotels')
def api_hotels():
    data = list(db.hotel.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/customers')
def api_customers():
    data = list(db.customer.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/rooms')
def api_rooms():
    data = list(db.room.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/suiterooms')
def api_suiterooms():
    data = list(db.suiteroom.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/bookings')
def api_bookings():
    data = list(db.booking.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/contains')
def api_contains():
    data = list(db.contains.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/payments')
def api_payments():
    data = list(db.payment.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)


@app.context_processor
def inject_active_db():
    return {"active_db": session.get("active_db", "mariadb")}

# Run the application with debug mode
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

