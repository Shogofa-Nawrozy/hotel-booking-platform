from flask import Flask, render_template, jsonify
from pymongo import MongoClient
import subprocess
import mysql.connector
from mysql.connector import Error

max_retries = 10
retry_delay = 3  # seconds

for attempt in range(max_retries):
    try:
        db = mysql.connector.connect(
            host="mariadb",
            user="root",
            password="root",
            database="hotelbooking"
        )
        print("Connected to MariaDB")
        break
    except Error as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(retry_delay)
else:
    print("Failed to connect after several attempts.")
    exit(1)

app = Flask(__name__)



@app.route('/admin')
def admin_dashboard():
    return render_template("admin.html")


@app.route('/import-mariadb')
def import_mariadb():
    # Run your seeder script
    result = subprocess.run(['python3', 'mariadb_seeder.py'], capture_output=True, text=True)

    if result.returncode == 0:
        return "<h2>✅ Fake data imported into MariaDB successfully!</h2><a href='/admin'>Back</a>"
    else:
        return f"<h2>❌ Error importing data:</h2><pre>{result.stderr}</pre><a href='/admin'>Back</a>"



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


client = MongoClient("mongodb://mongo:27017/")
db = client["hotel-booking-platform"]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about-us.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/rooms')
def rooms():
    return render_template('rooms.html')

@app.route('/room-details')
def rooms_details():
    return render_template('room-details.html')

@app.route('/bookings')
def bookings():
    return render_template('bookings.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/booking_report')
def booking_report():
    return render_template('booking_report.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog-details')
def blog_details():
    return render_template('blog-details.html')



# BACKEND API ROUTES (JSON Endpoints for all collections)

@app.route('/api/hotels')
def api_hotels():
    data = list(db.hotel.find())
    for d in data:
        d['_id'] = str(d['_id'])  # Convert ObjectId to string
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

