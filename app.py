from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from datetime import timedelta, datetime
import subprocess
import mysql.connector
import os  # Needed for environment variable access

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


# SHOGOFA CHANGES *********************************************************************************************************************
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customer WHERE Username=%s AND Password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['customer_id'] = user['CustomerID']
            return redirect(url_for('bookings'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')


# Booking list
@app.route('/bookings')
def bookings():
    customer_id = session.get('customer_id')
    if not customer_id:
        flash("Please log in to view your bookings.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            b.BookingID, b.TotalPrice, b.CheckInDate, b.CheckOutDate,
            r.RoomNumber, h.Name AS HotelName, h.Rating AS HotelRating,
            rv.Rating AS ReviewRating
        FROM Booking b
        JOIN Contains c ON b.BookingID = c.BookingID
        JOIN Room r ON c.HotelID = r.HotelID AND c.RoomNumber = r.RoomNumber
        JOIN Hotel h ON r.HotelID = h.HotelID
        LEFT JOIN Review rv ON rv.CustomerID = b.CustomerID AND rv.HotelID = h.HotelID
        WHERE b.CustomerID = %s
        ORDER BY b.BookingID DESC
    """, (customer_id,))
    bookings = cursor.fetchall()

    # Get payment status for each booking
    for booking in bookings:
        cursor.execute("SELECT PaymentStatus FROM Payment WHERE BookingID = %s", (booking['BookingID'],))
        payment_statuses = [row['PaymentStatus'] for row in cursor.fetchall()]
        if all(status == 'completed' for status in payment_statuses) and payment_statuses:
            booking['is_paid'] = True
        else:
            booking['is_paid'] = False
        booking['has_pending'] = any(status == 'pending' for status in payment_statuses)
    cursor.close()
    conn.close()
    return render_template('bookings.html', booking=bookings)

# Payments list
@app.route('/payment', methods=['GET', 'POST'])
def payment():
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

    # Fetch pending payment amount from Payment table
    pending_amount = None
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

    # Convert booking_total to float
    try:
        booking_total = float(booking_total)
    except (TypeError, ValueError):
        booking_total = 0.0

    return render_template(
        'payment.html',
        booking_id=booking_id,
        booking_total=booking_total,
        pending_amount=pending_amount
    )


# Booking report page
@app.route('/booking_report', methods=['GET', 'POST'])
def booking_report():
    filter_date = None
    if request.method == 'POST':
        filter_date = request.form.get('date')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            c.Name AS CustomerName,
            h.Name AS HotelName,
            COUNT(DISTINCT b.BookingID) AS NumBookings,
            COALESCE(SUM(p.Amount), 0) AS TotalSpent
        FROM Booking b
        JOIN Customer c ON b.CustomerID = c.CustomerID
        JOIN Contains co ON b.BookingID = co.BookingID
        JOIN Hotel h ON co.HotelID = h.HotelID
        LEFT JOIN Payment p ON b.BookingID = p.BookingID
        WHERE (%s IS NULL OR b.CheckInDate = %s)
        GROUP BY c.Name, h.Name
        ORDER BY c.Name, h.Name
    """, (filter_date, filter_date))
    report = cursor.fetchall()

    # Summary: total customers and total revenue
    cursor.execute("SELECT COUNT(DISTINCT CustomerID) AS TotalCustomers FROM Booking")
    total_customers = cursor.fetchone()['TotalCustomers']
    cursor.execute("SELECT COALESCE(SUM(Amount), 0) AS TotalRevenue FROM Payment")
    total_revenue = cursor.fetchone()['TotalRevenue']

    cursor.close()
    conn.close()
    return render_template(
        'booking_report.html',
        report=report,
        total_customers=total_customers,
        total_revenue=total_revenue,
        filter_date=filter_date
    )


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

# Reset MariaDB with dummy data
@app.route('/reset-mariadb')
def reset_mariadb():
    try:
        result = subprocess.run(['python3', 'mariadb_seeder.py'], capture_output=True, text=True)
        if result.returncode == 0:
            return render_template("admin.html", message="✅ MariaDB has been reset and repopulated with fake data.")
        else:
            return render_template("admin.html", message=f"❌ Error during MariaDB reset: {result.stderr}")
    except Exception as e:
        return render_template("admin.html", message=f"❌ Exception occurred: {str(e)}")

# Migrate data from MariaDB to MongoDB
@app.route('/migrate-sql-to-nosql')
def migrate_sql_to_nosql():
    try:
        result = subprocess.run(["python", "migrate_sql_to_nosql.py"], capture_output=True, text=True)
        if result.returncode == 0:
            return render_template("admin.html", message="✅ Data successfully migrated from MariaDB to MongoDB.")
        else:
            return render_template("admin.html", message=f"❌ Migration Error: {result.stderr}")
    except Exception as e:
        return render_template("admin.html", message=f"❌ Exception: {str(e)}")

# Switch to MariaDB
@app.route('/activate-mariadb')
def activate_mariadb():
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


# Run the application with debug mode
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
